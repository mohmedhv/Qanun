# Comparaison de la recherche — loi 90-11

Date d'exécution : 2026-11-25.

## Corpus et protocole

- Corpus P2 : 160 passages pour 158 articles distincts, chargés par `src.search.search_service.load_documents()` depuis les chunks du dépôt.
- Les articles 7 et 94 sont découpés en deux passages chacun; la métrique déduplique les résultats par citation d'article avant le top 3.
- Questions : les 10 lignes de `eval/questions.csv`; les références sont les numéros d'articles inscrits dans ce fichier.
- BM25 : l'index partagé `src.search.bm25_search.BM25Index`, `k1=1.5`, `b=0.75`.
- E5 : Disponible : modèle `intfloat/multilingual-e5-small`, 160 vecteurs de passages en cache; les 10 questions ont été encodées.
- Hit@3 vaut oui si au moins un article de référence apparaît dans les trois premiers articles distincts. P@3 divise les références trouvées par 3; R@3 les divise par le nombre de références attendues.
- Le résultat agrégé n'inclut que les questions `verified=oui` et dans le périmètre; Q08–Q09 restent visibles mais non vérifiées, Q10 est hors périmètre.
- Cette comparaison porte sur le corpus français original de 1990. Elle ne valide pas les versions historiques ni les références juridiques; Q09 (1997) est donc affichée, mais exclue de l'agrégat.
- Le calcul des embeddings est local et n'appelle aucun LLM ni API générative.

## Résultats par question

| ID | Références | Validation | BM25 top 3 | Hit@3 | P@3 | R@3 | E5 top 3 | Hit@3 | P@3 | R@3 |
|---|---|---|---|---:|---:|---:|---|---:|---:|---:|
| Q01 | 8, 9 | oui | 10, 63, 13 | non | 0/3 | 0/2 | 8, 9, 11 | oui | 2/3 | 2/2 |
| Q02 | 12, 13 | oui | 32, 47, 140 | non | 0/3 | 0/2 | 107, 96, 106 | non | 0/3 | 0/2 |
| Q03 | 18 | oui | 19, 18, 20 | oui | 1/3 | 1/1 | 18, 20, 19 | oui | 1/3 | 1/1 |
| Q04 | 22, 24 | oui | 22, 13, 31 | oui | 1/3 | 1/2 | 22, 23, 33 | oui | 1/3 | 1/2 |
| Q05 | 39, 40, 41, 42 | oui | 157, 64, 94 | non | 0/3 | 0/4 | 41, 40, 43 | oui | 2/3 | 2/4 |
| Q06 | 31, 32 | oui | 31, 32, 36 | oui | 2/3 | 2/2 | 32, 31, 36 | oui | 2/3 | 2/2 |
| Q07 | 73, 74 | oui | 82, 62, 27 | non | 0/3 | 0/2 | 113, 6, 5 | non | 0/3 | 0/2 |
| Q08 | 73, 74, 75 | a_verifier | 81, 83, 41 | non | 0/3 | 0/3 | 113, 53, 72 | non | 0/3 | 0/3 |
| Q09 | 12, 13 | a_verifier | 62, 27, 77 | non | 0/3 | 0/2 | 96, 97, 147 | non | 0/3 | 0/2 |
| Q10 | — | non_concerne | 68, 20, 66 | n/a | n/a | n/a | 68, 20, 51 | n/a | n/a | n/a |

## Résultats agrégés — questions vérifiées et dans le périmètre

| Méthode | Questions évaluées | Hit@3 | P@3 moyen | R@3 moyen |
|---|---:|---:|---:|---:|
| BM25 | 7/7 | 3/7 (42.9%) | 0.190 | 0.357 |
| E5 | 7/7 | 5/7 (71.4%) | 0.381 | 0.571 |

## Limites et reproduction

Les étiquettes `oui` viennent du fichier de questions et n'ont pas été revues par une seconde personne pendant ce calcul. Les références Q08 et Q09 restent à vérifier; Q10 sert de contrôle hors périmètre. Les scores mesurent le classement des références fournies, pas la justesse juridique.

Reproduction : exécuter `python -m eval.retrieval_comparison` depuis la racine. Le cache E5 des passages doit correspondre aux chunks chargés; `E5Index` le valide par identifiants et empreinte SHA-256 du corpus. Installer les dépendances de `requirements.txt` et disposer localement des poids `intfloat/multilingual-e5-small`.
