# RB-013 — Vault scellé (sealed) après redémarrage

## Symptômes

Les applications reçoivent l'erreur `503 Vault is sealed` : après un redémarrage, Vault
ne peut plus déchiffrer ses données tant qu'il n'est pas descellé.

## Résolution

1. Vérifier l'état :
   ```bash
   vault status
   ```
2. Appliquer la procédure VAULT-UNSEAL : le descellement demande 3 clés sur 5 (partage
   de Shamir), détenues par des gardiens différents. Chaque gardien saisit sa clé :
   ```bash
   vault operator unseal
   ```
3. Vérifier que `Sealed` vaut `false`.

## Règles

Ne jamais copier une clé de descellement dans un ticket, un chat ou un fichier.
