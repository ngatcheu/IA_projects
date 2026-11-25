# RB-035 — Dérive d'horloge NTP sur des serveurs

## Symptômes
Erreurs Kerberos, jetons JWT refusés, journaux d'audit désordonnés.

## Diagnostic
1. Mesurer l'écart : `chronyc tracking`.
2. La tolérance est de 500 ms.

## Résolution
Resynchroniser sur les serveurs NTP internes `ntp1.horizon.local` et `ntp2.horizon.local`.