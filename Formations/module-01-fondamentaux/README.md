# Module 1 — Fondamentaux

Partie A — RAG · jour 1 · 2 h · **statut : en cours**

Premier maillon du fil rouge : un RAG minimal. Le module 2 part de ce code et le fait évoluer.

```
module-01-fondamentaux/
├── cours.md             Cours 1
├── Dockerfile           image du module (Python 3.12, dépendances, modèle d'embedding)
├── docker-compose.yml   un service : rag
├── pyproject.toml       dépendances du module (+ uv.lock)
└── code/
    ├── prototype.py     RAG minimal : ingestion en mémoire + requête + Claude
    └── docs/            mini-corpus : 4 runbooks de la Banque Horizon
```

## Objectifs

- Expliquer les 4 limites d'un LLM seul que le RAG traite
- Distinguer ingestion (hors ligne) et requête (en ligne)
- Choisir entre RAG, fine-tuning, long context et prompt engineering

## Lancer le module

Depuis ce dossier, dans WSL. La clé API se met une seule fois dans `IA_projects/.env`
(partagé par tous les modules, ignoré par Git).

```bash
cd Formations/module-01-fondamentaux
docker compose build                     # une fois (et après un changement de dépendances)

# Sans clé API : la recherche seule (phase 2 jusqu'au prompt)
docker compose run --rm rag --recherche-seule "Combien de clés faut-il pour desceller Vault ?"

# RAG complet, passages affichés
docker compose run --rm rag --passages "Que signifie le code HZ-SEPA-404 et que faire ?"

# La même question au modèle seul, pour comparer (exercice 1)
docker compose run --rm rag --sans-rag "Que signifie le code HZ-SEPA-404 et que faire ?"
```

Le dossier `code/` est monté dans le conteneur : une modification de `prototype.py` est
prise en compte sans reconstruire l'image.

## Livrable : prototype RAG minimal

- [x] Ingestion : découpage par titres, embeddings, index en mémoire
- [x] Requête : recherche top-k, prompt ancré, réponse citée
- [x] Image Docker du module
- [ ] Exercices du [cours](cours.md) : niveau 1 (comprendre), niveau 2 (choisir),
  niveau 3 (pratiquer, dont 3 modifications de `prototype.py`)

## Ce que le module 2 fera évoluer

- La matrice NumPy en mémoire devient une **base vectorielle Qdrant** (service ajouté au
  docker-compose), avec collection versionnée.
- Comparaison de modèles d'embedding pour corriger l'échec de l'exercice 5.

## Notes et décisions

Résultats du 2026-11-24 (image `ia-projects/module-01:1.0.0`, `claude-opus-5-5`,
embeddings `paraphrase-multilingual-MiniLM-L12-v2`) :

| Exercice | Observation |
| --- | --- |
| 1. HZ-SEPA-404, RAG, k=3 | Les 3 passages viennent du bon runbook, mais la section **Résolution** (job `sepa-dispatch-retry`) n'est pas dedans (4ᵉ, score 0,51). Le modèle le dit honnêtement : « le contexte ne contient pas de procédure de résolution ». |
| 1. HZ-SEPA-404, RAG, k=4 | Section Résolution récupérée : réponse complète et citée (signification, cut-off 15h30, `sepa-dispatch-retry`, P1 au-delà de 1 000). |
| 1. HZ-SEPA-404, sans RAG | Le modèle reconnaît ne pas connaître ce code interne et ne fait que des hypothèses génériques, en le signalant : pas d'hallucination, mais pas de réponse utile. |
| 2. Vault, k=1 et k=3 | Bonne réponse dans les deux cas (3 clés sur 5). Avec k=3, la règle « ne jamais copier une clé » est ajoutée [2]. |
| 4. Livret A (hors corpus) | Refus propre : pas d'information dans le contexte, aucune invention de taux. Score du meilleur passage : 0,30. |
| 5. « redémarre en boucle » | Échec du retrieval : RB-001 absent du top 3. Avec « CrashLoopBackOff » : RB-001 en tête (0,63). |

Ce qu'on retient :

- **La réponse ne vaut que ce qu'on retrouve** : avec la même question et le même modèle,
  passer de k=3 à k=4 a changé une réponse incomplète en réponse complète.
- Le découpage par section isole « Résolution » du reste du runbook : un chunk
  parent-document (module 3) ou un reranker (module 4) éviterait ce piège.
- Le score du meilleur passage (0,30 pour le livret A, contre 0,53 à 0,70 pour les
  bonnes questions) pourrait servir de **seuil de refus** avant même d'appeler le
  modèle (module 5).
- L'échec de l'exercice 5 motive le module 2 (meilleur modèle d'embedding) et le
  module 4 (recherche hybride).
