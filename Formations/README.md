# Formation RAG et agents IA — suivi par module

Un dossier par module, **autonome** : cours, code, dépendances, Dockerfile et
docker-compose. Le fil rouge avance de module en module :

> **module N = copie du module N-1 + ce qu'apporte le cours N.**

On démarre avec un RAG minimal (module 1) et on arrive à l'agent d'analyse d'incident de
la Banque Horizon (module 17). Chaque dossier reste lançable seul : on peut revenir à
n'importe quelle étape et comparer deux modules (`diff -r module-01… module-02…`).

Démarrer un nouveau module :

```bash
cd Formations
cp -r module-01-fondamentaux/{Dockerfile,docker-compose.yml,pyproject.toml,uv.lock,.dockerignore,code} \
      module-02-embeddings-bases-vectorielles/
# puis faire évoluer le code, les dépendances et l'image dans le nouveau dossier
```

La clé API est partagée : `IA_projects/.env` (ignoré par Git), lu par tous les modules.

| Module | Jour | Livrable | Lab | Statut |
| --- | --- | --- | --- | --- |
| [01 — Fondamentaux](module-01-fondamentaux/) | 1 | Prototype RAG minimal | 1 | terminé |
| [02 — Embeddings et bases vectorielles](module-02-embeddings-bases-vectorielles/) | 1 | Index interrogeable | 1 | en cours |
| [03 — Ingestion : parsing, chunking, pipelines](module-03-ingestion-parsing-chunking/) | 1 | Pipeline d'ingestion incrémental | 2 | base posée |
| [04 — Retrieval avancé](module-04-retrieval-avance/) | 2 | Recherche hybride + reranker | 3 | à faire |
| [05 — Génération](module-05-generation/) | 2 | Prompt ancré avec citations | 4 | base posée |
| [06 — Évaluation du RAG](module-06-evaluation-rag/) | 2 | Golden set + rapport de métriques | 4 | base posée |
| [07 — RAG avancé](module-07-rag-avance/) | 3 | Choix argumenté d'une variante | exercice | à faire |
| [08 — Sécurité du RAG](module-08-securite-rag/) | 3 | Modèle de menaces + contrôles | 5 | à faire |
| [09 — Industrialisation sur Kubernetes](module-09-industrialisation-kubernetes/) | 3 | Déploiement GitOps | 10 | à faire |
| [10 — Agents avec LangGraph](module-10-agents-langgraph/) | 4 | Agent à graphe d'états + validation humaine | 6, 7 | à faire |
| [11 — Boucles agentiques](module-11-boucles-agentiques/) | 4 | Boucle bornée et mesurée | 7 | à faire |
| [12 — Outils, sorties structurées et MCP](module-12-outils-mcp/) | 5 | Outils typés et serveur MCP | 8 | à faire |
| [13 — Mémoire d'agent](module-13-memoire-agent/) | 5 | Mémoire court et long terme | 8 | à faire |
| [14 — Performance et coûts](module-14-performance-couts/) | 5 | Garde-fous de coût et routage | 9 | à faire |
| [15 — Fiabilité et récupération d'erreurs](module-15-fiabilite-erreurs/) | 6 | Chaîne de repli + injection de fautes | 9 | à faire |
| [16 — Évaluation et observabilité des agents](module-16-evaluation-observabilite-agents/) | 6 | Suite d'évaluation en CI | 10 | à faire |
| [17 — Cadre bancaire](module-17-cadre-bancaire/) | 7 | Matrice de risques + runbook | 10 + projet final | à faire |

Statuts : **à faire** → **base posée** (du code existe déjà) → **en cours** → **terminé**
(livrable produit et critère du lab atteint).
