# IA_projects — RAG et agents IA, de la plateforme à la production

Projet fil rouge de la [formation RAG et agents IA](fichier_formation.md) :
la plateforme d'agents internes de la **Banque Horizon** (banque fictive, données
synthétiques). Il démarre en assistant d'astreinte (RAG sur des runbooks) et devient,
module après module, l'**agent d'analyse d'incident**.

## Organisation : un module = un dossier autonome

Chaque module de [Formations/](Formations/README.md) contient son cours, son code, ses
dépendances, son Dockerfile et son docker-compose. **Le module N reprend le code du module
N-1 et le fait évoluer** : on peut lancer n'importe quelle étape seule et comparer deux
étapes.

```
Formations/
  module-01-fondamentaux/   cours.md, Dockerfile, docker-compose.yml, code/   ← on en est là
  module-02-…/              copie du module 1 + base vectorielle Qdrant
  …
  module-17-cadre-bancaire/ agent d'analyse d'incident complet
fichier_formation.md        support de cours complet
adr/                        journal des décisions (commun)
.env                        clé API partagée par les modules (ignoré par Git)
```

## Démarrage

Seul Docker est nécessaire (WSL ou Linux).

```bash
cp .env.example .env && nano .env        # ANTHROPIC_API_KEY, une seule fois
cd Formations/module-01-fondamentaux
docker compose build
docker compose run --rm rag --passages "Que signifie le code HZ-SEPA-404 et que faire ?"
```

Chaque module documente ses propres commandes dans son README.

## Code en attente de migration vers les modules

Le code ci-dessous a été écrit d'un bloc avant l'organisation par module. Il sera repris
dans les modules au fur et à mesure, puis supprimé de la racine :

| Élément | Module cible |
| --- | --- |
| `src/iaprojects/store.py`, `embeddings.py` (Qdrant, collection versionnée) | 2 |
| `src/iaprojects/chunking.py`, `ingest.py`, `corpus/`, `scripts/generate_runbooks.py`, `tests/` | 3 |
| `src/iaprojects/rag.py`, `llm.py` (sortie structurée, refus) | 5 |
| `evals/` (golden set, recall@k, seuil CI) | 6 |

`scripts/setup.sh` et `docker-compose.yml` (Qdrant) à la racine servent seulement à ce
code en attente.
