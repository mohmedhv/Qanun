# Rapport corrigé — suivi avant la semaine 3

Date de mise à jour : 25/11/2026. Échéance communiquée : vendredi 27/11/2026.

## Résultats vérifiés

| Élément | Résultat | Statut / limite |
|---|---|---|
| Loi 90-11 et en-têtes OCR | 158 fiches, numéros 1–158 sans trou. La passe stricte trouve 152 en-têtes; les six en-têtes mal lus sont 1, 30, 54, 82, 144 et 146. La passe contextuelle retrouve les 158 numéros. | Les six en-têtes ne sont pas six articles absents du texte OCR. Les lignes sources sont dans `docs/ocr_evidence/header_check_rerun.txt`. |
| Précision/rappel des en-têtes | TP=152, FP=1, FN=6; précision = 99,35 %, rappel = 96,20 %. | Comparaison occurrence par occurrence à la séquence JSON; le faux positif est le premier « Art. 148 », qui correspond à l'article 146. L'inventaire n'est pas une référence indépendante. Voir `docs/ocr.md`. |
| OCR sur trois pages du JO | PDF 2 / JO 488, PDF 3 / JO 489 et PDF 15 / JO 501 ont des transcriptions de référence et des copies OCR brutes séparées. CER : 4,413 %, 4,871 %, 8,120 %; WER : 11,597 %, 16,789 %, 14,458 %. | Brouillons visuels de l'assistant; pas encore relus par une deuxième personne. Les taux ne sont pas présentés comme une validation humaine. Détails dans `docs/ocr.md`. |
| Échantillon de 10 articles | 10 fiches sont marquées OK dans `docs/manual_check.md`. | Cette feuille compare le parseur à un PDF secondaire de 29 pages; elle ne vérifie pas ce PDF contre le JO officiel. |
| Passages P2 | `data/interim/chunks.json` contient 160 passages pour 158 articles; les articles 7 et 94 ont chacun deux passages. | La comparaison ci-dessous charge ces passages via le service de recherche P4. |
| BM25 sur les 10 questions | Sur les 7 questions marquées vérifiées et dans le périmètre : Hit@3 = 3/7 (42,9 %), P@3 moyen = 0,190, R@3 moyen = 0,357. | Résultats BM25 et par-question dans `docs/retrieval_comparison.md`. Les références des questions doivent encore être relues indépendamment. |
| E5 sur les 10 questions | Même corpus de 160 passages : Hit@3 = 5/7 (71,4 %), P@3 moyen = 0,381, R@3 moyen = 0,571. | Calcul local avec `intfloat/multilingual-e5-small`; aucun appel à une API LLM. Q08–Q09 restent non vérifiées et Q10 est hors périmètre. |
| Base SQLite locale | `data/db/qanun.db` existe localement, mais est ignorée par Git. Elle contient 158 articles et 160 passages; aucune table `versions` n'est présente. | Ce fichier n'est pas la source de la comparaison et n'est pas confirmé comme dernière base d'Ikram. Le benchmark utilise le JSON des passages. Ne pas le reconstruire par-dessus sans sauvegarde et accord P3. |
| Modifications de la loi | `P3_Modified_Articles.csv` contient 79 lignes : 36 `VERIFIED_OFFICIAL_JO`, 15 `VERIFIED_PUBLISHED_JO_COPY` et 28 `A_VERIFIER_SOURCE_OFFICIELLE`. | Les 28 lignes non vérifiées restent à vérifier; elles ne sont pas présentées comme des sources officielles confirmées. |
| Filtre des numéros UpGrowth | `eval/filter_labels.csv` contient 30 textes sans étiquette de pertinence. | Précision/rappel de ce filtre non calculables; état et tableau `n/a` dans `docs/filter_evaluation.md`. |
| Collecte et provenance | `docs/collection_rules.md` décrit l'index UpGrowth, les liens directs JORADP, les empreintes SHA-256, le délai de 3 secondes et le résultat robots.txt HTTP 404 relevé le 25/11/2026. | Les pages JORADP consultées ne précisent pas l'autorisation d'extraction automatisée; la note demande l'accord de l'enseignant avant une collecte en volume. |
| Modèle génératif | `openai/gpt-oss-120b` via Groq est indiqué dans le README et `config.example.yaml`. | Gemini n'est pas utilisé comme comparaison. |
| Corpus arabe | La version arabe repérée est scannée; aucun OCR arabe validé n'est présent. | Couverture arabe non garantie; collecte et validation restent à planifier. |

## Résultats de recherche par question

La table complète, avec les classements BM25/E5 et Hit@3, P@3 et R@3 pour chacune des 10 questions, est dans `docs/retrieval_comparison.md`. Reproduction : `python -m eval.retrieval_comparison` depuis la racine du dépôt. Les agrégats excluent explicitement les deux questions `a_verifier` et la question hors périmètre; ces exclusions ne sont pas des résultats à zéro.

## Travail restant avant remise

1. Faire relire par une deuxième personne les trois transcriptions OCR et confirmer les corrections proposées; elles sont encore des brouillons visuels.
2. Faire relire les références juridiques des 10 questions, en particulier Q08 et Q09, et conserver leur statut `a_verifier` jusqu'à confirmation.
3. Confirmer avec l'enseignant l'autorisation de toute collecte automatisée en volume. Le robots.txt répond actuellement 404; cela ne constitue pas une autorisation.
4. Confirmer avec Ikram la provenance de la base utilisée et faire fournir le dépôt/code P3 avec sa table `versions`; le fichier SQLite local ignoré n'est pas intégré à Git.
5. Vérifier les 28 lignes `A_VERIFIER_SOURCE_OFFICIELLE` sans modifier les CSV P3 avant validation par leur responsable.
6. Étiqueter les 30 textes du filtre UpGrowth avant d'en calculer précision et rappel.
7. Décider si le corpus arabe est accessible; sinon, conserver explicitement cette limite.
