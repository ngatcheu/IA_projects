# ADR 0001 — Stack des labs : Claude, embeddings locaux, Qdrant

- Date : 2026-11-23
- Statut : accepté
- Modules : 1, 2, 17

## Contexte

Les labs doivent tourner sur un laptop (WSL, 7 Go de RAM, sans GPU), puis être déployés
sur le cluster Kubernetes du homelab au Lab 10. La formation demande un client LLM
interchangeable (réversibilité, module 17).

## Décision

- **Génération** : API Claude, modèle `claude-opus-5-5` (variable `LLM_MODEL`), via un
  client unique (`src/iaprojects/llm.py`) avec repli serveur en cas de refus.
- **Embeddings** : modèle local multilingue via fastembed (ONNX, CPU) :
  `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions, 0,22 Go). Claude ne fournit
  pas d'embeddings ; un modèle local évite d'envoyer le corpus à un tiers.
- **Base vectorielle** : Qdrant (Docker Compose en local, StatefulSet au Lab 10).
  Collection nommée avec ses versions (`<corpus>_emb-<modèle>_chunk-<version>`) et alias
  stable pour la bascule bleu-vert.

## Conséquences

- Coût limité à la génération ; les embeddings sont gratuits et rejouables.
- Un modèle d'embedding de 384 dimensions est un point de départ : le Lab 3 comparera
  avec `multilingual-e5-large` (1024 dimensions) sur le golden set avant de changer.
- Changer de modèle d'embedding crée une nouvelle collection ; l'ancienne reste
  disponible pour un retour arrière.
