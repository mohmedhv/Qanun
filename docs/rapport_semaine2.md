# Rapport corrigé — état avant la semaine 3

Date : 23/11/2026. Échéance communiquée : vendredi 27/11/2026.

## Résumé des résultats vérifiables

| Élément | Résultat | Statut / limite |
|---|---|---|
| Base Loi 90-11 | 158 fiches structurées, numéros 1–158 sans trou numérique. | Fait pour le contrôle de séquence. La concordance intégrale avec le scan n'est pas démontrée. |
| Source utilisée pour l'évaluation | Le dossier ne contient pas de base SQLite construite; l'évaluation utilise les 158 fiches de `data/interim/articles.json`. | Confirmer que ce JSON correspond à la dernière base partagée par Ikram. |
| Échantillon manuel des articles | 10 articles marqués OK dans la feuille de contrôle; 0 divergence déclarée sur ces 10 fiches. | Fait selon `docs/manual_check.md`; ce n'est pas un taux OCR par page. |
| Chiffre « 152/158 » et liste des six absents | La passe stricte trouve 152 en-têtes sur 158; les six en-têtes mal détectés (1, 30, 54, 82, 144, 146) sont présents sous des formes OCR altérées. La passe tolérante retrouve 158/158; aucune perte de texte OCR n'est constatée. | Vérifié par `src/collect/check_ocr_articles.py`; voir aussi `docs/ocr.md` et `docs/ocr_evidence/ocr_header_check.txt`. |
| Cas de modification | 79 lignes au total : 36 vérifiées sur un JO officiel, 15 vérifiées sur une reproduction publiée, 28 à vérifier sur une source officielle. | Statut conservé par ligne dans `P3_Modified_Articles.csv`; ne pas présenter les 79 comme toutes vérifiées. |
| Références officiellement vérifiées | 51 lignes dans `P3_Officially_Checked_Examples.csv` : les 36 références JO 1996 et les 15 copies publiées de JO 1991/2022. | Fait dans ce périmètre; les 28 autres restent visibles à vérifier. |
| Recherche BM25 | Top 3 sur les 10 questions : 4/7 questions vérifiées et dans le périmètre ont au moins une référence attendue (Hit@3 = 57,1 %). | Fait; résultats par question, précision@3 et rappel@3 dans `docs/retrieval_comparison.md`. Q08–Q09 restent non vérifiées; Q10 hors périmètre. |
| Recherche par embeddings | Pas de score calculable dans cet environnement : `sentence-transformers` et les poids du modèle ne sont pas installés/localisés. | À exécuter avec un modèle d'embeddings autorisé et des poids locaux; le script n'effectue aucun téléchargement ni appel LLM. |
| Précision/rappel du filtre UpGrowth | 0 des 30 lignes de `eval/filter_labels.csv` ont une étiquette de pertinence. | À faire manuellement avant de calculer ces métriques; état documenté dans `docs/filter_evaluation.md`. |
| Collecte et provenance | 7 entrées au registre; les 7 empreintes locales correspondent au SHA-256 enregistré. Les couvertures des JO 2026 n° 52–57 confirment les numéros. | Le JO 1990 n° 17 est scanné : numéro imprimé à confirmer visuellement. robots/conditions restent à confirmer; voir `docs/collection_rules.md`. |
| Modèle génératif | Modèle imposé : `openai/gpt-oss-120b` via Groq, pour toutes les équipes. | README et exemple de configuration corrigés. Gemini ne sert pas de comparaison. |
| Corpus arabe | Pas de corpus arabe OCR validé; la version arabe repérée est scannée. | Collecte à la source et OCR/validation humaine restent à planifier; disponibilité du corpus non garantie. |

## Corrections apportées au dépôt

- Suppression des formulations de rapport non étayées par un résultat vérifiable.
- Ajout du rapport OCR avec distinction entre contrôle des 10 articles et taux d'erreur caractère sur trois pages.
- Ajout d'une comparaison BM25 reproductible sur les 158 articles et les 10 questions, avec Hit@3, P@3 et R@3 par question.
- Ajout des conditions d'utilisation observées, de la note robots.txt et de la chaîne de provenance depuis l'index UpGrowth jusqu'au PDF JORADP.
- Correction de la consigne du modèle Groq et résolution des marqueurs de conflit dans le journal et `.gitignore`.

## À terminer manuellement avant la semaine 3

1. Vérifier trois pages du PDF 1990 avec transcription indépendante et remplir le CER, les numéros d'articles trouvés/manquants et les corrections humaines dans `docs/ocr.md`.
2. Vérifier les 28 cas `A_VERIFIER_SOURCE_OFFICIELLE` sur les éditions officielles et maintenir leur statut individuel jusqu'à vérification.
3. Étiqueter la pertinence des 30 textes dans `eval/filter_labels.csv`; les métriques du filtre ne sont pas calculables avant cette étape.
4. Confirmer que `data/interim/articles.json` correspond à la dernière base partagée par Ikram; exporter les corrections récentes si nécessaire et relancer la comparaison.
5. Choisir/faire confirmer un modèle d'embeddings compatible avec la consigne de cours, installer ses dépendances et conserver les poids localement; relancer `python eval/retrieval_comparison.py`.
6. Confirmer avec l'enseignant si l'absence de robots.txt (404 rapporté le 21/11/2026) et l'absence de conditions explicites dans les pages JORADP consultées permettent les prochains téléchargements automatiques.
7. Décider si le corpus arabe est accessible; s'il ne l'est pas, documenter clairement cette limite au lieu de promettre une couverture arabe.

Les 28 cas non vérifiés doivent rester affichés comme « à vérifier » dans la base et les fichiers de rapport jusqu'à la vérification d'une source officielle.
