# Contrôle OCR et concordance avec la base

## État vérifiable dans le dépôt au 23/11/2026

| Contrôle | Constat | Statut |
|---|---|---|
| Fiches d'articles | `data/interim/articles.json` contient 158 fiches numérotées de 1 à 158; aucun numéro entier de cette séquence n'est absent ou dupliqué. | Contrôle de structure effectué |
| Échantillon d'articles | `docs/manual_check.md` consigne 10 articles avec texte, titre et paragraphes marqués OK, soit 0 divergence signalée sur 10 fiches dans cette feuille. | Contrôle manuel déclaré; les pages sources ne sont pas consignées |
| Concordance OCR sur 3 pages | Aucun OCR paginé et aucune transcription de référence page par page ne sont présents dans le dépôt. `data/raw/loi_90_11.txt` n'est pas aligné sur les pages du PDF original. | À faire; taux non calculable |
| Version arabe | Le rapport PDF indique une édition arabe scannée de 16 pages et 0 page avec texte extractible. | OCR arabe et validation humaine à faire; la collecte arabe n'est pas garantie |

## Rectification du chiffre « 152/158 »

Le chiffre « 152 articles sur 158 repérés » et la phrase « aucun article n'est perdu » ne sont pas étayés par les fichiers actuellement présents. Le JSON de la base possède les identifiants 1 à 158 sans trou numérique; il ne permet pas de prouver que chaque mot du PDF original a été reconnu correctement. La liste des six articles prétendument manquants n'est donc pas déductible du dépôt. Ne pas inventer ces six numéros : remplacer cette ancienne affirmation par le constat limité ci-dessus, puis faire la comparaison visuelle/OCR avant de conclure sur les pertes textuelles.

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
