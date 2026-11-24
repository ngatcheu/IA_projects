# Module 6 — Évaluation du RAG

Partie A — RAG · jour 2 · 2,5 h · **statut : base posée**

Cours : section « Module 6 » du [support de formation](../../fichier_formation.md).

## Objectifs

- Évaluer séparément retrieval (recall@k, MRR, nDCG) et génération (fidélité, pertinence)
- Construire et versionner un golden set
- Limites du LLM-as-judge, seuils bloquants en CI

## Livrable : Golden set + rapport de métriques

Pratique : **Lab 4** (voir le tableau des labs du support).

## Dans le projet fil rouge

- `evals/run.py` : recall@k + réussite, rapport JSON, code retour pour la CI
- `evals/golden/lab01.yaml` : 10 questions du Lab 1
- À venir : golden set de 50 questions (dont 10 sans réponse), Ragas, job GitLab CI

## Notes et décisions

_Notes de cours, difficultés rencontrées, ADR liés (`adr/`)._
