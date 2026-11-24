# Module 15 — Fiabilité et récupération d'erreurs

Partie B — Agents en production · jour 6 · 3 h · **statut : à faire**

Cours : section « Module 15 » du [support de formation](../../fichier_formation.md).

## Objectifs

- Retry avec backoff et jitter, chaîne de repli, auto-correction
- Récupération des hallucinations (ancrage, re-grounding, contradicteur, abstention)
- Tests de robustesse et post-incident

## Livrable : Chaîne de repli + tests d'injection de fautes

Pratique : **Lab 9** (voir le tableau des labs du support).

## Dans le projet fil rouge

- Déjà là : retries du SDK (`max_retries=4`), repli serveur sur refus (`fallbacks`)
- À venir : simulateur ServiceNow avec injection de fautes, chaîne de repli tracée

## Notes et décisions

_Notes de cours, difficultés rencontrées, ADR liés (`adr/`)._
