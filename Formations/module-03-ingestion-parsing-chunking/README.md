# Module 3 — Ingestion : parsing, chunking, pipelines

Partie A — RAG · jour 1 · 2,5 h · **statut : base posée**

Cours : section « Module 3 » du [support de formation](../../fichier_formation.md).

## Objectifs

- Parser PDF, tableaux, HTML en conservant la structure
- Choisir une stratégie de chunking (taille fixe, structure, parent-document…)
- Ingestion incrémentale, CDC, déduplication, masquage PII, dérive

## Livrable : Pipeline d'ingestion incrémental

Pratique : **Lab 2** (voir le tableau des labs du support).

## Dans le projet fil rouge

- `src/iaprojects/chunking.py` : découpage par titres + en-tête YAML de métadonnées
- `src/iaprojects/ingest.py` : ingestion idempotente par hash (ajout, mise à jour, suppression)
- À venir : tickets ServiceNow (JSON) et Confluence (HTML), CDC simulé, dédup MinHash, PII (Presidio)

## Notes et décisions

_Notes de cours, difficultés rencontrées, ADR liés (`adr/`)._
