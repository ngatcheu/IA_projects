"""Module 1 — prototype RAG minimal.

Les deux phases du cours, sans rien d'autre :
  1. INGESTION : runbooks Markdown -> découpage par titres -> embeddings -> matrice en mémoire
  2. REQUÊTE   : question -> embedding -> k passages les plus proches -> prompt -> Claude

Usage (depuis la racine du dépôt IA_projects) :
    uv run python Formations/module-01-fondamentaux/code/prototype.py "Que faire si Vault est scellé ?"
    ... --passages          affiche aussi les passages retrouvés et leur score
    ... --sans-rag          pose la question au modèle seul (comparaison, exercice 1)
    ... --recherche-seule   n'appelle pas Claude (aucune clé API nécessaire)
    ... -k 1                nombre de passages fournis au modèle

Pas de base vectorielle ici : une matrice NumPy suffit pour 4 documents. Qdrant arrive au
module 2, l'ingestion incrémentale au module 3, l'évaluation au module 6.
"""

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

import anthropic
import numpy as np
from dotenv import find_dotenv, load_dotenv
from fastembed import TextEmbedding

HERE = Path(__file__).resolve().parent
# Hors Docker : .env à la racine du dépôt (cherché en remontant les dossiers).
# Dans Docker : la clé arrive par docker-compose (env_file), il n'y a pas de .env.
load_dotenv(find_dotenv(usecwd=True))

MODEL = os.getenv("LLM_MODEL", "claude-opus-5-5")
MIN_SCORE = 0.35 # en dessous, la question est hors du périmètre des runbooks
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

SYSTEM = (
    "Tu es l'assistant d'astreinte de la Banque Horizon. "
    "Réponds uniquement à partir du contexte. Si l'information est absente, dis-le. "
    "Cite les sources [n] après chaque affirmation. Reprends les commandes et seuils "
    "exactement comme dans le contexte."
)


@dataclass
class Passage:
    source: str   # fichier d'origine
    section: str  # titre de la section
    text: str


# --------------------------------------------------------------------------- 1. INGESTION
def load_passages(docs_dir: Path) -> list[Passage]:
    """Découpe chaque runbook en sections de niveau 2 (## ...). Chaque passage garde le
    titre du document, pour rester compréhensible hors contexte."""
    passages = []
    for path in sorted(docs_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        for section in re.split(r"(?m)^(?=## )", text)[1:]:
            name = section.splitlines()[0].lstrip("# ").strip()
            passages.append(Passage(path.name, name, f"{title} — {section.strip()}"))
    return passages


class Index:
    """« Base vectorielle » minimale : une matrice de vecteurs normalisés."""

    def __init__(self, passages: list[Passage]):
        self.passages = passages
        self.model = TextEmbedding(EMBEDDING_MODEL)  # le MÊME modèle pour indexer et interroger
        self.vectors = self._embed([p.text for p in passages])

    def _embed(self, texts: list[str]) -> np.ndarray:
        v = np.array(list(self.model.embed(texts)))
        return v / np.linalg.norm(v, axis=1, keepdims=True)  # normalisés : cosinus = produit scalaire

    # ------------------------------------------------------------------- 2. REQUÊTE
    def search(self, question: str, k: int) -> list[tuple[Passage, float]]:
        q = self._embed([question])[0]
        scores = self.vectors @ q
        best = np.argsort(-scores)[:k]
        return [(self.passages[i], float(scores[i])) for i in best]


def build_prompt(question: str, hits: list[tuple[Passage, float]]) -> str:
    context = "\n\n".join(f"[{i}] (source : {p.source})\n{p.text}" for i, (p, _) in enumerate(hits, 1))
    return f"Contexte :\n{context}\n\nQuestion : {question}"


def generate(system: str, prompt: str) -> str:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY absente : la renseigner dans IA_projects/.env "
                         "(ou utiliser --recherche-seule)")
    response = anthropic.Anthropic().beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",                  # repli serveur si le filtre de sécurité refuse
        output_config={"effort": "low"},      # question factuelle : peu de réflexion suffit
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        return "(requête déclinée par le modèle)"
    return "".join(b.text for b in response.content if b.type == "text").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prototype RAG minimal (module 1)")
    parser.add_argument("--prompt", action="store_true", help="afficher le prompt sans appeler Claude")
    parser.add_argument("question")
    parser.add_argument("-k", type=int, default=3, help="nombre de passages (défaut : 3)")
    parser.add_argument("--passages", action="store_true", help="afficher les passages retrouvés")
    parser.add_argument("--sans-rag", action="store_true", help="interroger le modèle seul")
    parser.add_argument("--recherche-seule", action="store_true", help="ne pas appeler Claude")
    args = parser.parse_args()

    if args.sans_rag:
        print(generate("Tu es l'assistant d'astreinte de la Banque Horizon.", args.question))
        return

    index = Index(load_passages(HERE / "docs"))
    hits = index.search(args.question, args.k)

    if args.prompt:
        print(SYSTEM, "\n\n", build_prompt(args.question, hits))
        return
    
    if args.passages or args.recherche_seule:
        print("Passages retrouvés :")
        for i, (p, score) in enumerate(hits, 1):
            print(f"  [{i}] {score:.2f}  {p.source} — {p.section}")
        print()

    if hits[0][1] < MIN_SCORE:
        print("Je n'ai pas cette information dans les runbooks.")
        return
    
    if not args.recherche_seule:
        print(generate(SYSTEM, build_prompt(args.question, hits)))


if __name__ == "__main__":
    main()
