# RB-005 — Virements SEPA bloqués en statut PENDING

## Contexte

Les virements SEPA sortants passent par le service `svc-sepa` puis par la chambre de
compensation STEP2. Le cut-off STEP2 est à 15h30 : un virement non transmis avant cette
heure part le jour ouvré suivant.

## Symptômes

- Virements qui restent au statut PENDING.
- Code d'erreur `HZ-SEPA-404` renvoyé par le partenaire : le lot n'a pas été reçu.

## Résolution

1. Vérifier le nombre de virements en attente dans le tableau de bord SEPA.
2. Relancer le batch de dispatch avec le job Argo `sepa-dispatch-retry`.
3. Vérifier que le nombre de virements PENDING diminue.

## Escalade

Au-delà de 1 000 virements en attente, ouvrir un incident P1 et prévenir le back-office.
