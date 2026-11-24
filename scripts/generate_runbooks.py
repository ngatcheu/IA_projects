"""Rédige les runbooks synthétiques de corpus/topics.yaml avec Claude.

    uv run python scripts/generate_runbooks.py            # génère ceux qui manquent
    uv run python scripts/generate_runbooks.py --only RB-001 RB-004

Idempotent : un runbook déjà présent n'est pas régénéré (pas de coût inutile).
L'en-tête YAML (identifiant, service, droits) est écrit par le script, jamais par le
modèle : les métadonnées de gouvernance ne dépendent pas de la génération.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
import yaml

from iaprojects.config import settings
from iaprojects.llm import RefusedError, generate_text

SYSTEM = """Tu rédiges des runbooks d'exploitation pour l'équipe plateforme de la Banque
Horizon, une banque fictive. Tout est synthétique : aucune donnée réelle, aucun nom de
personne réelle.

Format : Markdown, en français, sans bloc de code englobant tout le document.
Structure obligatoire, dans cet ordre :
# <titre>
## Contexte
## Symptômes
## Diagnostic
## Résolution
## Escalade
## Références

Contraintes :
- Intègre TOUS les faits imposés, mot pour mot pour les codes, seuils, commandes et noms.
- Les commandes sont dans des blocs de code avec le langage (bash, sql...).
- Diagnostic et Résolution sont des étapes numérotées.
- N'invente pas d'autres codes d'erreur que ceux imposés.
- Entre 400 et 700 mots."""


def write_runbook(topic: dict, out_dir) -> str:
    body = generate_text(
        SYSTEM,
        f"Titre : {topic['title']}\nService : {topic['service']}\nFaits imposés : {topic['facts']}",
    )
    front = {
        "id": topic["id"],
        "title": topic["title"],
        "service": topic["service"],
        "classification": "interne",
        "allowed_groups": ["infra", "astreinte"],
        "source_system": "runbooks-generator",
    }
    path = out_dir / f"{topic['id']}.md"
    path.write_text("---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False) + "---\n" + body + "\n",
                    encoding="utf-8")
    return path.name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="identifiants à (re)générer")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    corpus = settings().corpus_dir
    topics = yaml.safe_load((corpus / "topics.yaml").read_text(encoding="utf-8"))["runbooks"]
    out_dir = corpus / "runbooks"
    out_dir.mkdir(exist_ok=True)

    if args.only:
        todo = [t for t in topics if t["id"] in set(args.only)]
    else:
        todo = [t for t in topics if not (out_dir / f"{t['id']}.md").exists()]
    print(f"{len(todo)} runbook(s) à générer avec {settings().llm_model}")

    failed = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(write_runbook, t, out_dir): t["id"] for t in todo}
        for f in as_completed(futures):
            try:
                print("  ok", f.result())
            except (anthropic.APIError, RefusedError) as exc:  # on continue, échecs listés à la fin
                failed.append(futures[f])
                print("  ÉCHEC", futures[f], type(exc).__name__, exc)
    if failed:
        raise SystemExit(f"échecs : {' '.join(sorted(failed))} (relancer le script)")


if __name__ == "__main__":
    main()
