# Contrôle OCR et concordance avec la base

## État vérifiable dans le dépôt au 23/11/2026

| Contrôle | Constat | Statut |
|---|---|---|
| Fiches d'articles | `data/interim/articles.json` contient 158 fiches numérotées de 1 à 158; aucun numéro entier de cette séquence n'est absent ou dupliqué. | Contrôle de structure effectué |
| Échantillon d'articles | `docs/manual_check.md` consigne 10 articles avec texte, titre et paragraphes marqués OK, soit 0 divergence signalée sur 10 fiches dans cette feuille. | Contrôle manuel déclaré; les pages sources ne sont pas consignées |
| Concordance OCR sur 3 pages | Le texte OCR brut `F1990017.txt` et son relevé de qualité existent localement; le texte OCR complet n'est pas versionné. Aucune transcription humaine alignée page par page n'est disponible. | À faire; CER non calculé faute de transcription humaine de référence |
| Version arabe | Le rapport PDF indique une édition arabe scannée de 16 pages et 0 page avec texte extractible. | OCR arabe et validation humaine à faire; la collecte arabe n'est pas garantie |

## Rectification du chiffre « 152/158 »

Le contrôle reproductible de `src/collect/check_ocr_articles.py` trouve 152 en-têtes stricts sur les 158 articles du JSON. Les six numéros sans en-tête strict sont 1, 30, 54, 82, 144 et 146. Ils sont tous présents dans le texte OCR sous des formes mal reconnues : « Article 1er », « Ârt. 30 », « Art. 54; », « Art. 82:+- », « Art ra » et « Art. 148 » lu pour 146 (le véritable article 148 apparaît plus loin). La passe tolérante, qui signale explicitement les deux interprétations contextuelles, retrouve 158 numéros sur 158 : 6 en-têtes mal détectés, 0 article perdu dans le texte OCR. Le détail des lignes brutes se trouve dans `docs/ocr_evidence/ocr_header_check.txt`.

## Taux à calculer après transcription de référence

Pour trois pages contenant le texte de la loi, comparer l'OCR brut à une transcription indépendante faite à la main. Consigner pour chaque page le numéro PDF et le numéro imprimé du JO, les articles présents, la transcription de référence, le texte OCR avant correction et chaque correction humaine.

- Taux d'erreur caractère (CER) = (substitutions + suppressions + insertions) / nombre de caractères de la transcription de référence.
- Exactitude caractère = 1 − CER.
- Ne pas compter une correction humaine comme une réussite OCR : garder le texte OCR brut, la correction signalée et l'identité/date de la vérification séparément.

| Page source | Articles repérés | Transcription humaine | OCR brut comparé | Substitutions / suppressions / insertions | CER | Vérificateur et date |
|---|---|---|---|---|---|---|
| 1 sur 3 — page à choisir dans `F1990017.pdf` | à relever | à transcrire | non disponible | non calculé | non calculé | à faire |
| 2 sur 3 — page à choisir dans `F1990017.pdf` | à relever | à transcrire | non disponible | non calculé | non calculé | à faire |
| 3 sur 3 — page à choisir dans `F1990017.pdf` | à relever | à transcrire | non disponible | non calculé | non calculé | à faire |

## Travail manuel restant

1. Ouvrir `F1990017.pdf`, repérer trois pages qui contiennent effectivement les articles de la loi et noter à la fois le numéro PDF et le numéro imprimé.
2. Transcrire ces pages sans copier le texte OCR; inclure les titres, les débuts d'articles, les « bis » éventuels, les mots collés ou coupés en fin de ligne et les paragraphes.
3. Comparer les transcriptions au texte OCR brut, puis enregistrer chaque écart avec le texte source, la lecture OCR et la correction proposée.
4. Compter les écarts et compléter le CER page par page. Faire vérifier les corrections par une autre personne.
5. Si une page contient un article absent de la base ou tronqué, inscrire son numéro exact et corriger la fiche correspondante en gardant une trace de la correction.

La feuille de 10 articles reste une preuve d'un échantillon d'articles, pas une mesure d'erreur OCR sur trois pages.
