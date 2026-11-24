# Module 2 — Embeddings et bases vectorielles

Partie A — RAG · jour 1 · 2,5 h · **statut : en cours**

Cours : section « Module 2 » du [support de formation](../../fichier_formation.md).

## Objectifs

- Choisir un modèle d'embedding multilingue et la similarité
- Comprendre HNSW, IVF, PQ et dimensionner un index
- Choisir la base (pgvector, Qdrant, Milvus, OpenSearch)

## Livrable : Index interrogeable

Pratique : **Lab 1** (voir le tableau des labs du support).

## Dans le projet fil rouge

- `src/iaprojects/embeddings.py` : embeddings locaux fastembed (multilingue)
- `src/iaprojects/store.py` : Qdrant, collection versionnée + alias (bleu-vert)
- `docker-compose.yml` : Qdrant local

## Notes et décisions

_Notes de cours, difficultés rencontrées, ADR liés (`adr/`)._
