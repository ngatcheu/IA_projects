# Module 8 — Sécurité du RAG

Partie A — RAG · jour 3 · 3 h · **statut : à faire**

Cours : section « Module 8 » du [support de formation](../../fichier_formation.md).

## Objectifs

- OWASP Top 10 LLM appliqué au RAG
- Contrôle d'accès dans la requête vectorielle (ACL au retrieval)
- Contrôles d'exploitation et red teaming en CI

## Livrable : Modèle de menaces + contrôles

Pratique : **Lab 5** (voir le tableau des labs du support).

## Dans le projet fil rouge

- Déjà là : `allowed_groups` et `classification` dans chaque chunk, règle anti-injection dans le prompt
- À venir : filtre de droits au retrieval, deux workspaces (RH, juridique), ticket piégé, tests en CI

## Notes et décisions

_Notes de cours, difficultés rencontrées, ADR liés (`adr/`)._
