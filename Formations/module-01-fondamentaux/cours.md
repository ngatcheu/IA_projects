# Cours 1 — Fondamentaux du RAG

Durée : 2 h · Livrable : prototype RAG minimal ([code/](code/))

Un RAG (*Retrieval-Augmented Generation*) donne à un LLM les passages utiles d'une base
de connaissances **au moment de la question**, au lieu de compter sur sa mémoire.

## 1. Pourquoi le RAG

Un LLM seul a quatre limites :

| Limite | Exemple à la Banque Horizon | Réponse du RAG |
| --- | --- | --- |
| **Connaissance figée** à la date d'entraînement | Le cut-off STEP2 est passé de 15h00 à 15h30 le mois dernier | On réindexe le runbook modifié, sans réentraîner |
| **Aucun accès** aux données privées | Le modèle n'a jamais vu le code d'erreur `HZ-SEPA-404` | Le passage du runbook est fourni dans le prompt |
| **Hallucinations** : réponse plausible même sans la connaître | Il invente une commande `sepa-retry --force` qui n'existe pas | Consigne « réponds uniquement à partir du contexte », refus sinon |
| **Aucune traçabilité** | Impossible de dire d'où vient le seuil de 1 000 virements | Chaque affirmation cite sa source `[n]` |

Le RAG répond aux quatre : les documents sont **à jour, privés et cités**.

> Démonstration : `python code/prototype.py --sans-rag "..."` pose la question au modèle
> seul ; sans l'option, la même question passe par le RAG. Comparer les deux réponses.

## 2. Les deux phases

```
INGESTION (hors ligne, quand les documents changent)
  sources ──► parsing ──► chunking ──► embeddings ──► index vectoriel (+ métadonnées)

REQUÊTE (en ligne, à chaque question)
  question ──► embedding ──► recherche des k passages proches
           ──► prompt = consignes + passages numérotés + question
           ──► LLM ──► réponse + sources [n]
```

1. **Ingestion** : on prépare les documents une fois, puis à chaque modification.
   Le module 3 la rend incrémentale ; ici on se contente de découper par titres.
2. **Requête** : à chaque question, on cherche, on construit le prompt, on génère.

Point clé : la question et les passages sont vectorisés par **le même modèle
d'embedding**, sinon les vecteurs ne sont pas comparables (module 2).

## 3. RAG, fine-tuning ou long context

| Besoin | Approche adaptée | Raison |
| --- | --- | --- |
| Faits changeants, privés, traçables | **RAG** | Mise à jour sans réentraîner, citations, droits d'accès |
| Style, format, vocabulaire métier, tâche précise | Fine-tuning | Change le comportement, pas la base de faits |
| Petit corpus (quelques documents) | Long context | Simple, mais coût et latence proportionnels au contexte |
| Cadrer le ton ou le format | Prompt engineering | Aucune infrastructure |

Les approches se combinent : fine-tuning pour le comportement, RAG pour les faits.

**Cas de l'astreinte** : 50 runbooks qui changent, des procédures à citer mot pour mot,
des droits d'accès (certains documents réservés à l'équipe infra) → **RAG**. Avec 4
runbooks seulement, le long context suffirait : c'est ce que montre l'exercice 3.

## 4. Le prototype minimal

Le code du module ([code/prototype.py](code/prototype.py)) suit exactement ce schéma :

```python
def answer(question: str) -> str:
    q_vec = embed(question)                     # 1. vectoriser la question
    chunks = vector_store.search(q_vec, k=5)    # 2. chercher les 5 passages proches
    context = "\n\n".join(f"[{i+1}] {c.text}" for i, c in enumerate(chunks))
    prompt = (
        "Réponds uniquement à partir du contexte. "
        "Si l'information est absente, dis-le. Cite les sources [n].\n\n"
        f"Contexte :\n{context}\n\nQuestion : {question}"
    )
    return llm.generate(prompt)                 # 3. générer
```

Volontairement simple : l'« index » est une matrice en mémoire et la recherche un produit
scalaire. La base vectorielle (Qdrant) arrive au module 2, l'ingestion incrémentale au
module 3, l'évaluation au module 6.

## À retenir

La qualité d'un RAG dépend **d'abord de ce qu'on retrouve**, ensuite de ce que le modèle
écrit. Une mauvaise réponse vient le plus souvent d'un mauvais passage récupéré : avant
d'accuser le modèle, regarder les passages (option `--passages` du prototype).

## Exercices

Chercher d'abord, puis cliquer sur « Voir le corrigé ». Les commandes se lancent depuis le
dossier du module (`docker compose run --rm rag ...`, voir le [README](README.md)).

### Niveau 1 — Comprendre

**1.1** Quelles sont les quatre limites d'un LLM seul que le RAG traite ?

<details><summary>Voir le corrigé</summary>

Connaissance figée, aucun accès aux données privées, hallucinations, absence de
traçabilité.
</details>

**1.2** QCM — Le RAG ne corrige **pas** une de ces limites. Laquelle ?
a) Le modèle ignore les procédures internes · b) Le modèle répond avec un ton trop
familier · c) Le modèle ne dit pas d'où vient une information · d) Le modèle ignore une
procédure modifiée la semaine dernière

<details><summary>Voir le corrigé</summary>

**b.** Le ton et le style relèvent du prompt engineering ou du fine-tuning : le RAG
apporte des **faits**, il ne change pas le comportement du modèle. a) et d) sont
traités par les documents fournis, c) par les citations.
</details>

**1.3** Pourquoi la question et les documents doivent-ils être vectorisés par le même
modèle d'embedding ?

<details><summary>Voir le corrigé</summary>

Chaque modèle produit son propre espace de vecteurs. Comparer un vecteur du modèle A à un
vecteur du modèle B n'a aucun sens, même à dimension égale. Conséquence pratique : changer
de modèle d'embedding impose de **tout réindexer** (module 2).
</details>

**1.4** Remettre dans l'ordre les étapes de la phase **requête** : génération ·
recherche des k passages · construction du prompt · embedding de la question ·
réponse avec sources.

<details><summary>Voir le corrigé</summary>

Embedding de la question → recherche des k passages → construction du prompt
(consignes + passages numérotés + question) → génération → réponse avec sources.
</details>

**1.5** Vrai ou faux : « Une réponse fausse vient le plus souvent du modèle de langage. »

<details><summary>Voir le corrigé</summary>

**Faux.** Elle vient le plus souvent d'un **mauvais passage récupéré** : le modèle ne peut
pas citer ce qu'on ne lui a pas donné. On commence toujours le diagnostic par les passages
(`--passages`). L'exercice 3.1 le montre.
</details>

### Niveau 2 — Choisir

**2.1** Pour chaque besoin de la Banque Horizon, choisir entre RAG, fine-tuning, long
context et prompt engineering, et justifier en une phrase :
a) Un assistant qui répond sur les 2 000 procédures internes, mises à jour chaque semaine.
b) Un chatbot client qui doit toujours répondre avec le ton de la marque, en vouvoyant.
c) Résumer un contrat de 30 pages que l'utilisateur vient de déposer.
d) Classer chaque ticket entrant parmi 40 catégories métier, avec un vocabulaire très
spécifique et 100 000 tickets historiques étiquetés.

<details><summary>Voir le corrigé</summary>

a) **RAG** : beaucoup de documents, qui changent, et qu'il faut citer.
b) **Prompt engineering** (consignes de ton dans le prompt système) ; le fine-tuning
seulement si le prompt ne suffit pas.
c) **Long context** : un seul document, qui tient dans le contexte ; rien à indexer.
d) **Fine-tuning**, ou un petit classifieur entraîné : c'est une tâche précise et
répétitive, avec beaucoup d'exemples étiquetés. Le module 12 parle de ces routeurs
d'intention.
</details>

**2.2** (Exercice 3 de la première version) **Long context ou RAG ?** Nos 4 runbooks font
environ 460 mots. Estimer leur taille en tokens, puis pour 50 et 5 000 runbooks d'environ
600 mots. À partir de quand le RAG devient-il nécessaire ? Repère : en français, 1 token ≈
0,75 mot ; prix d'entrée de `claude-opus-5-5` : 4 $ par million de tokens.

<details><summary>Voir le corrigé</summary>

| Corpus | Tokens environ | Coût d'entrée par question, tout le corpus dans le prompt |
| --- | --- | --- |
| 4 runbooks | 600 | 0,0024 $ |
| 50 runbooks | 40 000 | 0,16 $ |
| 5 000 runbooks | 4 000 000 | impossible : dépasse le contexte (1 million de tokens) |

- À 4 runbooks, le long context est plus simple et suffit.
- À 50, c'est possible ; le **prompt caching** (module 14) réduirait fortement le coût,
  mais la latence et le bruit augmentent, et le modèle exploite moins bien le milieu d'un
  long contexte (module 5).
- À 5 000, le RAG est obligatoire. Avec le RAG, on envoie environ 3 passages, soit à peu
  près 1 000 tokens par question, quelle que soit la taille du corpus.

Le RAG reste aussi nécessaire, même avec un petit corpus, dès qu'il faut **filtrer par
droits d'accès** (un utilisateur ne doit pas recevoir un document RH) : le long context
envoie tout à tout le monde (module 8).
</details>

### Niveau 3 — Pratiquer avec le prototype

**3.1** Poser « Que signifie le code HZ-SEPA-404 et que faire ? » avec `--passages`
(k=3 par défaut), puis avec `--passages -k 4`. Que change le passage supplémentaire ?

<details><summary>Voir le corrigé</summary>

À k=3, les passages retenus sont Symptômes, Contexte et Escalade de RB-005 : la section
**Résolution** (job `sepa-dispatch-retry`) n'arrive qu'en 4ᵉ position (score 0,51). Le
modèle le dit honnêtement : « le contexte ne contient pas de procédure de résolution ». À
k=4, la réponse devient complète et citée.

Leçon : avec le même modèle, **la réponse ne vaut que ce qu'on retrouve**. Le découpage par
section a séparé « Résolution » du reste ; des chunks plus larges (parent-document,
module 3) ou un reranker (module 4) corrigent ce problème mieux qu'un k plus grand, qui
ajoute aussi du bruit.
</details>

**3.2** Poser la même question avec `--sans-rag`. Que fait le modèle seul ?

<details><summary>Voir le corrigé</summary>

Il dit ne pas connaître ce code interne et propose seulement des hypothèses génériques,
en les signalant comme telles (« 404 : par analogie avec HTTP, introuvable »). Il ne cite
ni `sepa-dispatch-retry`, ni le seuil de 1 000 virements, ni le cut-off de 15h30, car il
ne peut pas les connaître.

Un modèle moins prudent aurait pu inventer une procédure plausible : c'est
l'hallucination. Le RAG apporte les faits privés et la traçabilité.
</details>

**3.3** Poser « Combien de clés faut-il pour desceller Vault ? » avec `-k 1` puis `-k 3`.
Le bon passage est-il toujours en tête ? Qu'apporte k=3 ?

<details><summary>Voir le corrigé</summary>

Oui : la section Résolution de RB-013 est en tête dans les deux cas (score 0,53), et la
réponse est juste (3 clés sur 5, partage de Shamir). Avec k=3, le passage « Règles » est
aussi fourni et le modèle ajoute la consigne de sécurité « ne jamais copier une clé dans
un ticket ». Un k plus grand peut compléter la réponse, mais il coûte des tokens et
risque de diluer les bons passages.
</details>

**3.4** Poser « Quel est le taux du livret A ? » avec `--passages`. Le prototype doit
répondre qu'il n'a pas l'information. Relever le score du meilleur passage.

<details><summary>Voir le corrigé</summary>

Le modèle refuse proprement : l'information n'est pas dans le contexte, il n'invente pas
de taux. Le meilleur passage (RB-048, Objectifs) n'a qu'un score de **0,30**, contre 0,53 à
0,70 pour les questions couvertes par le corpus. Le modèle a quand même été appelé pour
rien : c'est l'objet de l'exercice 3.7.
</details>

**3.5** Avec `--recherche-seule`, poser « Un pod redémarre en boucle, comment voir les
logs de l'exécution précédente ? », puis la même question avec « CrashLoopBackOff ».
Expliquer l'écart.

<details><summary>Voir le corrigé</summary>

Avec « redémarre en boucle », RB-001 n'apparaît pas dans le top 3 : on obtient RB-048,
RB-005 et RB-013 (scores 0,36 à 0,44). Avec « CrashLoopBackOff », RB-001 occupe les 3
places (0,61 à 0,63).

Le petit modèle d'embedding multilingue (384 dimensions) rapproche mal le français
courant du jargon Kubernetes. Deux corrections viennent plus tard : un meilleur modèle
d'embedding (module 2) et la recherche hybride avec BM25, qui retrouve les mots exacts
(module 4). En attendant, réécrire la question avant la recherche est une parade
(module 4, « transformation de la requête »).
</details>

**3.6** *(code)* Ajouter une option `--prompt` qui affiche le prompt complet envoyé au
modèle, sans l'appeler.

<details><summary>Voir le corrigé</summary>

Dans `main()`, ajouter l'argument puis l'afficher avant l'appel à `generate` :

```python
parser.add_argument("--prompt", action="store_true", help="afficher le prompt sans appeler Claude")
...
if args.prompt:
    print(SYSTEM, "\n\n", build_prompt(args.question, hits))
    return
```

Test : `docker compose run --rm rag --prompt "Combien de clés pour desceller Vault ?"`.
On voit les consignes, les passages numérotés `[1]`, `[2]`… et la question : c'est
exactement ce que lit le modèle. Le dossier `code/` est monté, il n'y a pas d'image à
reconstruire.
</details>

**3.7** *(code)* Ajouter un **seuil de refus** : si le meilleur passage a un score
inférieur à 0,35, répondre « Je n'ai pas cette information dans les runbooks. » sans
appeler Claude. Vérifier avec la question du livret A et une question couverte.

<details><summary>Voir le corrigé</summary>

```python
MIN_SCORE = 0.35   # à calibrer : 0,30 hors sujet contre 0,53 et plus pour les bonnes questions

# dans main(), après hits = index.search(...)
if hits[0][1] < MIN_SCORE:
    print("Je n'ai pas cette information dans les runbooks.")
    return
```

Livret A : refus immédiat, aucun appel payant. Vault : réponse normale.

Limite : le seuil est fixé à l'œil sur quelques questions. Le module 6 le calibrera sur
un golden set. Trop haut (0,5 par exemple), il refuse des questions légitimes mal
formulées ; trop bas, il laisse passer les questions hors sujet. Et le seuil ne détecte
pas tout : « redémarre en boucle » (meilleur score 0,44) passe le seuil alors que le bon
runbook n'a pas été trouvé.
</details>

**3.8** *(code)* Ajouter un 5ᵉ runbook `code/docs/RB-035-ntp.md` sur la dérive d'horloge
NTP (tolérance 500 ms, commande `chronyc tracking`, serveurs `ntp1.horizon.local` et
`ntp2.horizon.local`), avec des sections `##`. Poser « Quelle est la tolérance de dérive
d'horloge ? ». Faut-il reconstruire l'image ?

<details><summary>Voir le corrigé</summary>

Un exemple de runbook :

```markdown
# RB-035 — Dérive d'horloge NTP sur des serveurs

## Symptômes
Erreurs Kerberos, jetons JWT refusés, journaux d'audit désordonnés.

## Diagnostic
1. Mesurer l'écart : `chronyc tracking`.
2. La tolérance est de 500 ms.

## Résolution
Resynchroniser sur les serveurs NTP internes ntp1.horizon.local et ntp2.horizon.local.
```

La question retrouve RB-035 en tête et la réponse cite 500 ms. **Pas de reconstruction** :
`code/` est monté dans le conteneur et le prototype réindexe tout le dossier à chaque
lancement. C'est simple pour 5 documents, mais coûteux pour 5 000 : le module 3 rendra
l'ingestion incrémentale (on ne recalcule que ce qui a changé).
</details>
