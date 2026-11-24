# RB-001 — Pod en CrashLoopBackOff sur le cluster k8s-prod-par1

## Contexte

Un pod en CrashLoopBackOff redémarre en boucle : le conteneur démarre, échoue, et
Kubernetes attend de plus en plus longtemps avant de le relancer. Les applications de la
Banque Horizon tournent dans des namespaces `apps-<appli>`.

## Diagnostic

1. Identifier le pod et le nombre de redémarrages :
   ```bash
   kubectl -n apps-<appli> get pods
   ```
2. Lire les événements du pod :
   ```bash
   kubectl -n apps-<appli> describe pod <pod>
   ```
3. Lire les journaux de l'exécution précédente (celle qui a échoué) :
   ```bash
   kubectl -n apps-<appli> logs <pod> --previous
   ```
4. Un code de sortie 137 (`OOMKilled`) indique un dépassement de la limite mémoire.

## Escalade

Au-delà de 5 redémarrages en 10 minutes, ouvrir un incident P2 et prévenir l'équipe
propriétaire de l'application.
