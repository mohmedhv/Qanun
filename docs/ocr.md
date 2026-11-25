# Contrôle OCR et concordance avec la base

## État vérifiable dans le dépôt au 25/11/2026

| Contrôle | Constat | Statut |
|---|---|---|
| Fiches d'articles | `data/interim/articles.json` contient 158 fiches numérotées de 1 à 158; aucun numéro entier de cette séquence n'est absent ou dupliqué. | Contrôle de structure effectué |
| Échantillon d'articles | `docs/manual_check.md` consigne 10 articles avec texte, titre et paragraphes marqués OK, soit 0 divergence signalée sur 10 fiches dans cette feuille. | Contrôle manuel déclaré; les pages sources ne sont pas consignées |
| Concordance OCR sur 3 pages | Les pages PDF 2, 3 et 15 (JO 488, 489 et 501) ont une transcription visuelle de référence et une copie OCR brute versionnées dans `docs/ocr_evidence/`. | CER/WER calculés; relecture humaine indépendante encore requise |
| Version arabe | Le rapport PDF indique une édition arabe scannée de 16 pages et 0 page avec texte extractible. | OCR arabe et validation humaine à faire; la collecte arabe n'est pas garantie |

## Rectification du chiffre « 152/158 »

Le contrôle reproductible de `src/collect/check_ocr_articles.py` trouve 152 en-têtes stricts sur les 158 articles du JSON. Les six numéros sans en-tête strict sont 1, 30, 54, 82, 144 et 146. Ils sont tous présents dans le texte OCR sous des formes mal reconnues : « Article 1er », « Ârt. 30 », « Art. 54; », « Art. 82:+- », « Art ra » et « Art. 148 » lu pour 146 (le véritable article 148 apparaît plus loin). La passe tolérante, qui signale explicitement les deux interprétations contextuelles, retrouve 158 numéros sur 158 : 6 en-têtes mal détectés, 0 article perdu dans le texte OCR. Le détail des lignes brutes se trouve dans `docs/ocr_evidence/ocr_header_check.txt`.

## Échantillon OCR : transcription de référence et résultats

Les pages ont été choisies pour couvrir le début, le corps et la fin de la loi : PDF 2 / JO 488 (articles 1 à 5), PDF 3 / JO 489 (articles 6 à 13; l'article 13 continue sur la page suivante) et PDF 15 / JO 501 (articles 155 à 158). Les transcriptions ont été rédigées en lisant les scans de `data/raw_pdf/F1990017.pdf`, puis comparées aux fichiers OCR bruts. Elles constituent un brouillon visuel préparé par l'assistant, pas une transcription humaine indépendante ni une référence relue à l'aveugle. Les taux sont donc indicatifs jusqu'à validation par une autre personne.

- Taux d'erreur caractère (CER) = (substitutions + suppressions + insertions) / nombre de caractères de la transcription de référence.
- Taux d'erreur mot (WER) = (substitutions + suppressions + insertions) / nombre de mots de la transcription de référence.
- Exactitude caractère = 1 − CER.
- `eval/ocr_cer.py` normalise uniquement les espaces (séquences d'espaces ramenées à un espace). La ponctuation, les accents, les en-têtes et les défauts d'ordre des colonnes restent comptés.
- Les traits d'union de fin de ligne ont été recomposés dans les références (ex. `économi-` / `ques` devient `économiques`); le moteur OCR peut donc être pénalisé s'il les conserve.
- Les copies OCR brutes et les transcriptions de référence sont conservées séparément. Une correction manuelle ne compte pas comme une réussite du moteur OCR.

| Page PDF / page JO | Articles repérés | Transcription de référence | OCR brut comparé | Caractères S / D / I | CER | WER | Relecteur et date |
|---|---|---|---|---:|---:|---:|---|
| 2 / 488 | 1–5 | [`F1990017_page_002_reference.txt`](ocr_evidence/transcriptions/F1990017_page_002_reference.txt) | [`F1990017_page_002_ocr_raw.txt`](ocr_evidence/raw/F1990017_page_002_ocr_raw.txt) | 30 / 36 / 93 | 0,044130 (3 603 caractères) | 0,115966 (595 mots) | Assistant, lecture visuelle; 25/11/2026; à relire |
| 3 / 489 | 6–13 (art. 13 partiel) | [`F1990017_page_003_reference.txt`](ocr_evidence/transcriptions/F1990017_page_003_reference.txt) | [`F1990017_page_003_ocr_raw.txt`](ocr_evidence/raw/F1990017_page_003_ocr_raw.txt) | 35 / 37 / 135 | 0,048706 (4 250 caractères) | 0,167894 (679 mots) | Assistant, lecture visuelle; 25/11/2026; à relire |
| 15 / 501 | 155–158 | [`F1990017_page_015_reference.txt`](ocr_evidence/transcriptions/F1990017_page_015_reference.txt) | [`F1990017_page_015_ocr_raw.txt`](ocr_evidence/raw/F1990017_page_015_ocr_raw.txt) | 8 / 63 / 97 | 0,081199 (2 069 caractères) | 0,144578 (332 mots) | Assistant, lecture visuelle; 25/11/2026; à relire |

Les copies brutes sont des duplicatas octet pour octet des fichiers locaux `data/processed/ocr/F1990017/page_002.txt`, `page_003.txt` et `page_015.txt`. Les écarts visuels relevés sont consignés dans [`F1990017_corrections.md`](ocr_evidence/F1990017_corrections.md). Le contrôle d'en-têtes recalculé se trouve dans [`header_check_rerun.txt`](ocr_evidence/header_check_rerun.txt). Aucun fichier OCR source ni fiche de `data/interim/` n'a été modifié.

## Relecture et corrections à finaliser

1. Faire relire les trois références directement sur les scans par une autre personne; elles ne constituent pas encore un étalon humain validé.
2. Confirmer les corrections consignées dans `docs/ocr_evidence/F1990017_corrections.md` avant de les appliquer aux textes exploités par le projet.
3. Si la relecture révèle un article absent ou tronqué dans une fiche, noter son numéro et faire corriger cette fiche séparément avec une trace de provenance.

La feuille de 10 articles reste une preuve d'un échantillon d'articles, pas une mesure d'erreur OCR sur trois pages. Le CER/WER présenté ici porte sur trois pages et inclut les erreurs de mise en page et d'ordre des colonnes.
