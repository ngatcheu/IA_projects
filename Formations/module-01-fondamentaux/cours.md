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

### Les mots du schéma

**Hors ligne / en ligne.** *Hors ligne* : le travail se fait à l'avance, en tâche de
fond, sans utilisateur qui attend (on peut prendre plusieurs minutes). *En ligne* : le
travail se fait pendant que l'utilisateur attend sa réponse (il faut quelques secondes).

Phase d'ingestion :

| Mot | Définition | Dans le prototype |
| --- | --- | --- |
| **Sources** | Les documents d'origine qu'on veut rendre interrogeables : runbooks, PDF, pages wiki, tickets… | Les 4 fichiers Markdown de `code/docs/` |
| **Parsing** | Lire le format du fichier (PDF, Word, HTML…) et en extraire le texte propre et sa structure (titres, tableaux), sans la mise en page | Rien à faire : le Markdown est déjà du texte (module 3 pour les PDF) |
| **Chunking** (découpage) | Couper chaque document en **passages** (*chunks*) assez courts pour être précis, assez longs pour avoir du sens. Un chunk est l'unité que l'on retrouve et que l'on donne au modèle | Une section `## …` = un passage, préfixé du titre du runbook |
| **Embedding** (vectorisation) | Transformer un texte en **vecteur** : une liste de nombres qui représente son **sens**. Deux textes de sens proche donnent des vecteurs proches, même avec des mots différents | Modèle local `paraphrase-multilingual-MiniLM-L12-v2` (fastembed), 384 nombres par passage |
| **Index vectoriel** | La structure qui stocke tous les vecteurs et permet de retrouver vite les plus proches d'un vecteur donné | Une simple matrice NumPy en mémoire (Qdrant au module 2) |
| **Métadonnées** | Les informations rangées **à côté** de chaque vecteur : document d'origine, section, date, droits d'accès… Elles servent à citer la source et à filtrer | Champs `source` (nom du fichier, ex. `RB-013-vault-sealed.md`) et `section` (titre de la section) de la classe `Passage` |

Phase de requête :

| Mot | Définition | Dans le prototype |
| --- | --- | --- |
| **Question** | Le texte posé par l'utilisateur, en langage naturel | L'argument passé en ligne de commande |
| **Embedding de la question** | La question est vectorisée **par le même modèle** que les passages, pour être comparable | `index.search()` appelle le même `TextEmbedding` |
| **Recherche des k passages proches** | Comparer le vecteur de la question à ceux de l'index et garder les **k** plus proches. La proximité se mesure par la **similarité cosinus** : un score de 1 (même sens) à 0 (aucun rapport) en pratique | Produit scalaire sur des vecteurs normalisés ; `k = 3` par défaut, option `-k` |
| **Score** | La valeur de similarité d'un passage avec la question. Il classe les passages et indique si la question est couverte par le corpus | Affiché avec `--passages` (≈ 0,5 à 0,7 si couvert, ≈ 0,3 sinon) |
| **Prompt** | Le texte complet envoyé au LLM. Ici : consignes + passages numérotés + question | Consignes dans `SYSTEM`, passages et question assemblés par `build_prompt()` |
| **Consignes** (prompt système) | Les règles de comportement données au modèle : répondre uniquement à partir du contexte, dire si l'information manque, citer `[n]` | La constante `SYSTEM`, envoyée à part comme prompt système |
| **Passages numérotés** | Les k passages retrouvés, chacun précédé de `[1]`, `[2]`… pour que le modèle puisse les citer | Construits dans `build_prompt()` |
| **LLM** (*Large Language Model*) | Le modèle de langage qui lit le prompt et **génère** la réponse, mot après mot. Il ne voit que le prompt : rien d'autre de la base | `claude-opus-5-5` via l'API Claude, fonction `generate()` |
| **Réponse + sources [n]** | Le texte final, où chaque affirmation renvoie au passage qui la justifie. On peut vérifier, et l'absence d'information se voit | Ce qu'affiche le prototype |

Les deux phases se rejoignent dans **l'index vectoriel** : l'ingestion l'écrit, la
requête le lit.

### C'est quoi l'indexation ?

**Indexer, c'est faire à l'avance le travail coûteux (découper, vectoriser, ranger), pour
que chaque question ne coûte qu'une recherche rapide.** C'est la phase d'ingestion.

Analogie : l'index à la fin d'un livre technique (« Vault → p. 42, 87 ; SEPA → p. 13 »).
Quelqu'un l'a construit **une fois** ; grâce à lui on trouve la bonne page sans relire
300 pages. En RAG, on range les passages non pas par **mots** mais par **sens** (vecteurs).

```
runbooks ──► découpage en passages ──► embedding de chaque passage ──► rangement dans l'index
 (.md)       (une section ## = 1)       (384 nombres par passage)       (vecteur + source + section)
```

À la question, on vectorise la question et on cherche les vecteurs les plus proches : on
ne relit jamais les documents.

**Dans le prototype**, c'est la ligne `index = Index(load_passages(HERE / "docs"))` de
`main()`. L'index est une matrice NumPy **en mémoire** :

- il est **reconstruit à chaque lancement** (c'est pourquoi un runbook ajouté est pris en
  compte tout de suite, exercice 3.8) ;
- il **disparaît** à la fin du programme.

Acceptable pour 5 runbooks, pas pour 5 000 : il faudrait recalculer des milliers
d'embeddings à chaque question.

**Au module 2**, l'index est stocké dans **Qdrant** (base vectorielle) :

- on indexe **une fois**, l'index est **conservé** entre les lancements ;
- ajouter un document = **l'indexer explicitement**, sinon il reste invisible ;
- changer de modèle d'embedding = **tout réindexer** (question 1.3), d'où la collection
  versionnée + alias ;
- la recherche reste rapide sur des millions de vecteurs grâce à des structures comme
  **HNSW**, alors que la matrice NumPy compare la question à **tous** les vecteurs un
  par un.

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

- **a)** Le modèle ignore les procédures internes
- **b)** Le modèle répond avec un ton trop familier
- **c)** Le modèle ne dit pas d'où vient une information
- **d)** Le modèle ignore une procédure modifiée la semaine dernière

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

Image : chaque modèle range les sens sur sa propre « carte ». Sur la carte du modèle A,
« Vault scellé » est peut-être en haut à gauche ; sur celle du modèle B, au même endroit,
il peut y avoir « virement SEPA ». Les axes ne veulent pas dire la même chose d'une carte
à l'autre. Une similarité cosinus entre un point de A et un point de B donne donc un
nombre sans signification, et sans aucune erreur Python si les dimensions sont égales
(384 par exemple) : le bug est silencieux, seuls les résultats sont faux.

C'est pour cela qu'au module 2, la base Qdrant utilise une **collection versionnée + un
alias** : on construit la nouvelle collection avec le nouveau modèle à côté de
l'ancienne, puis on bascule l'alias d'un coup (déploiement bleu-vert), sans mélanger les
deux espaces.
</details>

**1.4** Remettre dans l'ordre les étapes de la phase **requête** : génération ·
recherche des k passages · construction du prompt · embedding de la question ·
réponse avec sources.

<details><summary>Voir le corrigé</summary>

Embedding de la question → recherche des k passages → construction du prompt
(consignes + passages numérotés + question) → génération → réponse avec sources.

1. **Embedding de la question** : la question devient un vecteur.
2. **Recherche des k passages** : les k vecteurs les plus proches dans l'index.
3. **Construction du prompt** : consignes + passages numérotés `[1]`, `[2]`… + question.
4. **Génération** : le modèle lit ce prompt et rédige la réponse.
5. **Réponse avec sources** : la réponse cite les `[n]`.

Piège fréquent : placer la génération avant la construction du prompt. Le modèle ne voit
**que le prompt** ; il ne peut rien générer tant qu'on ne lui a pas donné le texte à lire.
La génération est donc forcément l'avant-dernière étape. L'option `--prompt` de
l'exercice 3.6 affiche exactement ce que lit le modèle.
</details>

**1.5** Vrai ou faux : « Une réponse fausse vient le plus souvent du modèle de langage. »

<details><summary>Voir le corrigé</summary>

**Faux.** Elle vient le plus souvent d'un **mauvais passage récupéré** : le modèle ne peut
pas citer ce qu'on ne lui a pas donné. On commence toujours le diagnostic par les passages
(`--passages`). L'exercice 3.1 le montre.

Pourquoi : le modèle ne voit **que le prompt** (question 1.4). Si la recherche ne lui
donne pas le bon passage, il n'a que deux comportements possibles :
- dire « l'information n'est pas dans le contexte » : c'est le bon comportement, mais la
  réponse est incomplète ;
- compléter avec sa mémoire : c'est une hallucination, que les consignes cherchent
  justement à empêcher.

Méthode de diagnostic à retenir : devant une mauvaise réponse, regarder **d'abord les
passages** (`--passages`), ensuite seulement le modèle. À l'exercice 3.1, avec k=3, la
section « Résolution » de RB-005 n'est pas retrouvée : le modèle dit honnêtement qu'il
n'a pas la procédure. Le modèle n'y est pour rien, c'est la recherche qui a raté.
</details>

### Niveau 2 — Choisir

**2.1** Pour chaque besoin de la Banque Horizon, choisir entre RAG, fine-tuning, long
context et prompt engineering, et justifier en une phrase :

- **a)** Un assistant qui répond sur les 2 000 procédures internes, mises à jour chaque
  semaine.
- **b)** Un chatbot client qui doit toujours répondre avec le ton de la marque, en
  vouvoyant.
- **c)** Résumer un contrat de 30 pages que l'utilisateur vient de déposer.
- **d)** Classer chaque ticket entrant parmi 40 catégories métier, avec un vocabulaire
  très spécifique et 100 000 tickets historiques étiquetés.

<details><summary>Voir le corrigé</summary>

- **a) RAG** : beaucoup de documents, qui changent, et qu'il faut citer.
- **b) Prompt engineering** (consignes de ton dans le prompt système) ; le fine-tuning
  seulement si le prompt ne suffit pas.
- **c) Long context** : un seul document, qui tient dans le contexte ; rien à indexer.
- **d) Fine-tuning**, ou un petit classifieur entraîné : c'est une tâche précise et
  répétitive, avec beaucoup d'exemples étiquetés. Le module 12 parle de ces routeurs
  d'intention.

Pour bien choisir, il faut aussi savoir **pourquoi les autres approches ne conviennent
pas** :

- **a)** Le long context est impossible : 2 000 procédures dépassent la fenêtre de
  contexte et coûteraient très cher à chaque question. Le fine-tuning serait à refaire
  chaque semaine et ne donnerait aucune citation.
- **b)** Le RAG apporte des faits, pas un ton (question 1.2). Une consigne dans le prompt
  système (« vouvoie, ton de la marque ») suffit le plus souvent et ne demande aucune
  infrastructure.
- **c)** Le document vient d'être déposé : l'indexer pour une seule utilisation n'a pas
  d'intérêt. 30 pages, c'est environ 20 000 tokens, qui tiennent largement dans le
  contexte. Le modèle lit tout, sans risquer de rater un passage à la recherche.
- **d)** Ce n'est pas une question de faits à retrouver, donc pas de RAG : c'est un
  **comportement** à apprendre (ranger dans la bonne case). Le prompt engineering avec
  40 catégories et un vocabulaire spécifique atteint vite ses limites. Les 100 000
  exemples étiquetés sont exactement ce dont un fine-tuning a besoin, et un modèle
  spécialisé est plus rapide et moins cher par ticket.

Règle : **beaucoup de documents qui changent → RAG ; un seul document → long context ;
le ton → prompt ; une tâche répétitive avec beaucoup d'exemples → fine-tuning.**
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

Méthode de calcul, cas par cas :

- **4 runbooks** : 460 ÷ 0,75 ≈ 613 tokens ; 4 × 613 ÷ 1 000 000 ≈ **0,0025 $**. Vérification
  rapide : 4 $ le million de tokens = 0,004 $ les mille ; 613 tokens ≈ 0,6 × 0,004 $.
- **50 runbooks** : 50 × 600 = 30 000 mots ; 30 000 ÷ 0,75 = 40 000 tokens ;
  4 × 40 000 ÷ 1 000 000 = **0,16 $**. À 500 questions par jour, c'est 80 $ par jour,
  environ 2 400 $ par mois, en entrée seulement, et chaque question fait lire 40 000
  tokens au modèle (latence).
- **5 000 runbooks** : 5 000 × 600 = 3 000 000 mots ; 3 000 000 **÷** 0,75 = 4 000 000
  tokens. Le calcul donne 16 $, mais la question est **impossible** : 4 fois la fenêtre
  de contexte, l'API refuse la requête. Au-delà d'une certaine taille, la question n'est
  plus « combien ça coûte » mais « est-ce que ça rentre ».
- **Avec le RAG** : environ 3 passages, soit 1 000 tokens, donc **0,004 $** par question,
  quelle que soit la taille du corpus.

Où passe la limite exactement ? Un runbook de 600 mots fait 800 tokens ;
1 000 000 ÷ 800 = **1 250 runbooks** remplissent toute la fenêtre, sans place pour la
question ni pour la réponse. En pratique, le RAG est :

- **inutile** pour quelques documents (sauf droits d'accès) ;
- **recommandé** dès quelques dizaines (coût, latence, bruit) ;
- **obligatoire** au-delà d'environ 1 000 runbooks, et pas seulement à 5 000.
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

À k=3, le modèle **n'invente pas** de procédure : il donne ce qu'il a (signification du
code, escalade, cut-off) et signale ce qui manque (« consultez les sections du runbook
RB-005 qui ne figurent pas dans le contexte »). C'est exactement le comportement demandé
par les consignes, et une illustration de la question 1.5 : la réponse est incomplète à
cause de la **recherche**, pas du modèle.

Pourquoi « Résolution » arrive-t-elle dernière, alors que c'est elle qui répond à « que
faire » ?

- **Symptômes (0,70)** contient le code `HZ-SEPA-404` mot pour mot et explique sa
  signification : c'est le cœur de la question.
- **Contexte (0,60)** et **Escalade (0,53)** parlent de virements SEPA et de PENDING,
  le même champ lexical que la question.
- **Résolution (0,51)** ne mentionne ni le code ni sa signification : elle parle de
  tableau de bord, de job Argo et de batch. Le seul lien avec la question est « que
  faire », trop vague pour peser dans le vecteur.

Les quatre scores restent proches (0,51 à 0,70) parce que chaque passage est préfixé du
titre du runbook (« Virements SEPA bloqués en statut PENDING »), qui les rapproche tous
de la question. Une question qui mélange deux intentions (« que signifie » **et** « que
faire ») produit un seul vecteur, dominé par la partie la plus spécifique (le code). La
décomposer en deux sous-questions est une autre parade (module 4, transformation de la
requête).
</details>

**3.2** Poser la même question avec `--sans-rag`. Que fait le modèle seul ?

<details><summary>Voir le corrigé</summary>

Il dit ne pas connaître ce code interne et propose seulement des hypothèses génériques,
en les signalant comme telles (« 404 : par analogie avec HTTP, introuvable »). Il ne cite
ni `sepa-dispatch-retry`, ni le seuil de 1 000 virements, ni le cut-off de 15h30, car il
ne peut pas les connaître.

Un modèle moins prudent aurait pu inventer une procédure plausible : c'est
l'hallucination. Le RAG apporte les faits privés et la traçabilité.

Comparé au runbook (« le lot n'a pas été reçu »), ses hypothèses sont fausses (IBAN
inconnu, mandat inexistant…), mais il les **présente comme telles** (« interprétation
probable, à confirmer ») : ce n'est pas une hallucination, c'est une prudence bien
calibrée.

Le vrai problème est **l'utilité en astreinte**. Mise en situation : 15h10, 1 200
virements bloqués. Le modèle seul propose cinq vérifications génériques et renvoie vers
« l'équipe propriétaire ». Il ne peut pas dire :

- qu'il reste **20 minutes** avant le cut-off STEP2 de 15h30, sinon les virements partent
  le jour ouvré suivant ;
- qu'au-delà de 1 000 virements, il faut **ouvrir un P1** tout de suite ;
- que l'action est de **relancer `sepa-dispatch-retry`**.

Avec le RAG, ces trois informations arrivent en quelques secondes, citées. Une réponse
honnête mais générique n'est pas une réponse **actionnable**.
</details>

**3.3** Poser « Combien de clés faut-il pour desceller Vault ? » avec `-k 1` puis `-k 3`.
Le bon passage est-il toujours en tête ? Qu'apporte k=3 ?

<details><summary>Voir le corrigé</summary>

Oui : la section Résolution de RB-013 est en tête dans les deux cas (score 0,53), et la
réponse est juste (3 clés sur 5, partage de Shamir). Avec k=3, le passage « Règles » est
aussi fourni et le modèle ajoute la consigne de sécurité « ne jamais copier une clé dans
un ticket ». Un k plus grand peut compléter la réponse, mais il coûte des tokens et
risque de diluer les bons passages.

Comment lire la sortie : **k = le nombre de passages donnés au modèle**, et le modèle ne
voit que ceux-là. RB-013 a 3 sections, donc 3 passages possibles :

| Passage | Score | k=1 | k=3 | Utilisé dans la réponse ? |
| --- | --- | --- | --- | --- |
| Résolution | 0,53 | ✅ | ✅ | oui, `[1]` : 3 clés sur 5, procédure |
| Règles | 0,52 | | ✅ | oui, `[2]` : « ne jamais copier une clé » |
| Symptômes | 0,31 | | ✅ | **non** : aucun `[3]` dans la réponse |

En une phrase : **augmenter k apporte plus d'informations utiles, mais aussi plus
d'informations inutiles.** Ici, Règles complète la réponse, Symptômes est envoyé pour
rien (des tokens payés, et du bruit qui peut embrouiller le modèle). Le bon k est un
compromis, que le module 6 apprendra à **mesurer** plutôt qu'à choisir au jugé.
</details>

**3.4** Poser « Quel est le taux du livret A ? » avec `--passages`. Le prototype doit
répondre qu'il n'a pas l'information. Relever le score du meilleur passage.

<details><summary>Voir le corrigé</summary>

Le modèle refuse proprement : l'information n'est pas dans le contexte, il n'invente pas
de taux. Le meilleur passage (RB-048, Objectifs) n'a qu'un score de **0,30**, contre 0,53 à
0,70 pour les questions couvertes par le corpus. Le modèle a quand même été appelé pour
rien : c'est l'objet de l'exercice 3.7.

Le score sert de **signal** : la recherche renvoie **toujours** k passages, même quand
aucun ne parle du sujet. Elle ne dit jamais « rien trouvé » ; c'est le score qui le dit.

| Question | Meilleur score | Couverte par les runbooks ? |
| --- | --- | --- |
| HZ-SEPA-404 (3.1) | 0,70 | oui |
| Vault (3.3) | 0,53 | oui |
| Livret A (3.4) | 0,30 | **non** |

Appeler le modèle quand même **est un problème**, même s'il refuse bien :

- **coût** : on paie un appel (et les tokens des passages hors sujet) pour une réponse
  connue d'avance ;
- **latence** : l'utilisateur attend plusieurs secondes pour « je ne sais pas » ;
- **risque** : ici le modèle refuse, mais rien ne le garantit. Avec des passages
  vaguement liés, un modèle peut être tenté d'en tirer une réponse, ou de répondre de
  mémoire (un taux du livret A d'il y a deux ans, par exemple).

Mieux vaut ne pas appeler le modèle du tout : c'est le **seuil de refus** de
l'exercice 3.7.
</details>

**3.5** Avec `--recherche-seule`, poser « Un pod redémarre en boucle, comment voir les
logs de l'exécution précédente ? », puis la même question avec « CrashLoopBackOff ».
Expliquer l'écart.

<details><summary>Voir le corrigé</summary>

Avec « redémarre en boucle », RB-001 n'apparaît pas dans le top 3 : on obtient RB-048,
RB-005 et RB-013 (scores 0,36 à 0,44). Avec « CrashLoopBackOff », RB-001 occupe les 3
places (0,58 à 0,61).

Le petit modèle d'embedding multilingue (384 dimensions) rapproche mal le français
courant du jargon Kubernetes. Deux corrections viennent plus tard : un meilleur modèle
d'embedding (module 2) et la recherche hybride avec BM25, qui retrouve les mots exacts
(module 4). En attendant, réécrire la question avant la recherche est une parade
(module 4, « transformation de la requête »).

Le plus surprenant : la section Contexte de RB-001 contient **mot pour mot** « Un pod en
CrashLoopBackOff redémarre en boucle », et pourtant la première question ne la retrouve
pas. Un embedding **n'est pas une recherche de mots** : il résume tout le passage en un
seul vecteur. Or chaque passage de RB-001 commence par le titre « Pod en
CrashLoopBackOff sur le cluster k8s-prod-par1 » et contient du jargon (`kubectl`,
namespaces, `OOMKilled`). Ce jargon tire le vecteur vers une zone « Kubernetes
technique » ; la question en français courant atterrit ailleurs. Autre écart : la
question dit « logs », le runbook dit « journaux ».

À l'inverse, le mot rare « CrashLoopBackOff » apparaît dans le titre, donc au début de
**chacun** des 3 passages : c'est pour cela que RB-001 occupe tout le top 3 avec des
scores proches. La bonne réponse (`kubectl logs <pod> --previous`) est dans la section
Diagnostic.

Leçon : les embeddings trouvent des passages **de sens proche** même sans mots communs
(c'est leur force), mais un petit modèle peut aussi rater un passage qui contient les
mots exacts (c'est leur faiblesse). D'où la recherche **hybride** du module 4 :
embeddings + BM25 (mots exacts).
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

**Où placer le bloc ?** C'est tout l'exercice. `main()` s'exécute de haut en bas :

```
hits = index.search(...)          ← hits existe à partir d'ici
    ► if args.prompt: ... return  ← seule place correcte
if not args.recherche_seule:
    print(generate(...))          ← appel payant à éviter
```

- **Trop haut** (avant la recherche) : `UnboundLocalError: cannot access local variable
  'hits'`. On ne peut pas construire le prompt avant d'avoir cherché les passages.
- **Trop bas** (après `generate`) : pas d'erreur, le prompt s'affiche… mais **après** la
  réponse de Claude. L'appel payant a déjà eu lieu ; le `return` arrive trop tard.

Lire un traceback **de bas en haut** : la dernière ligne dit *quoi* (le type d'erreur),
la ligne au-dessus dit *où* (fichier, ligne, `^^^^` sous le coupable), le haut dit
*comment on est arrivé là*.

Ce que montre la sortie : les consignes `SYSTEM`, puis chaque passage avec son numéro
`[n]`, sa source et le titre du runbook collé devant (voilà pourquoi tous les passages
d'un même runbook se ressemblent, exercice 3.5), puis la question. **Le modèle ne voit
rien d'autre.**
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

Pièges rencontrés en codant : placer le refus **après** l'affichage des passages (avec
`--passages`, on voit le score, puis le refus : on comprend pourquoi) et **avant**
l'appel à `generate` (sinon on paie l'appel). `hits[0]` est le meilleur couple
`(passage, score)` car la liste est triée ; `hits[0][1]` est son score.

| Question | Meilleur score | Bon runbook trouvé ? | Le seuil (0,35)… |
| --- | --- | --- | --- |
| Vault | 0,53 | oui | laisse passer : ✅ correct |
| Livret A | 0,30 | sans objet (hors sujet) | refuse : ✅ correct |
| « Redémarre en boucle » | 0,44 | **non** | laisse passer : ❌ |

Le seuil répond à « **existe-t-il un passage un peu proche ?** », pas à « **est-ce le
bon passage ?** ». Il détecte les questions **hors sujet**, pas les **mauvaises
recherches** sur une question couverte. Dans le 3ᵉ cas, Claude reçoit RB-048, RB-005 et
RB-013 et dira (au mieux) qu'il n'a pas l'information, alors qu'elle existe dans RB-001.
Le seuil est un **garde-fou de coût**, pas une garantie de qualité : celle-ci vient d'une
meilleure recherche (modules 2 et 4) et se **mesure** sur un golden set (module 6).
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

Résultat obtenu : Diagnostic 0,63, Symptômes 0,46, Résolution 0,38 ; réponse « 500 ms
[1] », avec `chronyc tracking` [1] et les serveurs NTP [3]. Le runbook est retrouvé
**sans aucune autre modification** : ni code, ni configuration.

Pourquoi pas de reconstruction ? Deux raisons, qu'il faut avoir toutes les deux :

1. **Le volume** : dans `docker-compose.yml`, la ligne `- ./code:/module/code` monte le
   dossier `code/` de la machine dans le conteneur. Le conteneur lit les fichiers du
   disque, pas une copie figée dans l'image.
2. **L'index en mémoire** : le prototype relit `code/docs/` et recalcule tous les
   embeddings **à chaque lancement** (`Index(load_passages(...))` dans `main()`). Il n'y a
   aucun index enregistré qui serait devenu périmé.

À l'inverse, il **faut** reconstruire l'image (`docker compose build`) quand on change
ce qui est **copié dans l'image** : les dépendances (`pyproject.toml`, `uv.lock`), le
`Dockerfile`, ou le modèle d'embedding préchargé.

Au module 2, l'index sera stocké dans Qdrant : ajouter un document demandera alors une
étape d'**ingestion** explicite, sinon il restera invisible.

Bonne pratique Markdown : mettre noms de serveurs et commandes entre backticks
(`` `ntp1.horizon.local` ``), pas entre apostrophes ; le modèle les recopie alors tels
quels. Sur AZERTY : AltGr + 7, puis Espace.
</details>
