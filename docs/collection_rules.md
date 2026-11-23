# Règles de collecte et provenance

Date de mise à jour de cette note : 2026-11-23.

## Sources et conditions consultées

| Source | Usage | Licence / conditions observées | Vérifié le |
|---|---|---|---|
| [UpGrowth — Index du Journal officiel](https://www.upgrowth.dz/datasets/journal-officiel-1962-2026) | Index CSV des numéros et liens directs vers les PDF de JORADP | CC BY 4.0 pour l'index seulement. Citer UpGrowth, lier la licence et signaler les modifications. Cette licence ne couvre pas les PDF du Journal officiel. | 2026-11-23 |
| [JORADP / Secrétariat général du Gouvernement](https://www.joradp.dz/HFR/Accueil.htm) | Source primaire des numéros et PDF officiels | La page d'accueil présente l'accès aux numéros et la recherche thématique. La page d'aide décrit la consultation, la recherche et l'impression; aucune autorisation générale de réutilisation automatisée n'y est formulée. Les conditions de collecte restent à confirmer. | 2026-11-23 |

Pages JORADP consultées : [accueil](https://www.joradp.dz/HFR/Accueil.htm) et [aide](https://www.joradp.dz/hfr/help.htm). L'aide explique comment consulter un numéro et rechercher/imprimer un texte. Aucune page de conditions générales couvrant l'extraction automatisée n'a été trouvée dans ces pages.

## robots.txt de joradp.dz

- URL : https://www.joradp.dz/robots.txt
- Résultat : le retour de l'enseignant du 21/11/2026 indique que le fichier est absent (HTTP 404). L'outil de consultation utilisé pour cette note n'a pas pu relire cette URL le 23/11/2026; le 404 est donc attribué au contrôle rapporté par l'enseignant.
- Contenu : aucun fichier robots.txt à citer selon ce contrôle.
- Téléchargement automatique de `/FTP/` : **à confirmer**. Un 404 ne donne pas de règle robots et les pages consultées ne précisent pas les droits d'extraction automatisée. Demander l'accord de l'enseignant avant toute nouvelle collecte en volume.

## Comportement du téléchargeur

- Délai minimum : 3 secondes entre téléchargements (`src/collect/downloader.py`).
- User-Agent : `QanunStudentProject/0.1 (university course project, polite crawler)`.
- Le code consulte robots.txt et refuse une URL interdite.
- Le registre conserve URL source, nom du fichier, année, numéro, langue, SHA-256 et date de téléchargement. Le registre actuel ne conserve pas la réponse HTTP de robots.txt; garder la preuve du contrôle séparément jusqu'à ce que ce champ soit ajouté.
- Le registre empêche un deuxième téléchargement d'un fichier déjà présent.

## Chaîne de provenance des fichiers présents

La chaîne suivie est : index UpGrowth → lien direct vers le domaine officiel `joradp.dz` → fichier nommé selon l'année et le numéro → empreinte SHA-256 et date dans `data/processed/download_registry.csv`. Les URLs de ce registre pointent toutes vers des chemins JORADP `FTP/jo-francais/<année>/F<année><numéro>.pdf`. L'index est attribué à UpGrowth; les PDF officiels ne sont ni couverts par la licence CC BY 4.0 d'UpGrowth ni redistribués dans le dépôt.

| Année | JO | Fichier du registre | Pages | État texte déclaré dans le registre | Vérification de provenance |
|---:|---:|---|---:|---|---|
| 1990 | 17 | `F1990017.pdf` | 15 | scan (0 caractère extractible sur les 3 premières pages) | SHA-256 local identique au registre; numéro imprimé sur la couverture à confirmer visuellement |
| 2026 | 52 | `F2026052.pdf` | 24 | texte | Couverture locale « N° 52 »; SHA-256 local identique au registre |
| 2026 | 53 | `F2026053.pdf` | 24 | texte | Couverture locale « N° 53 »; SHA-256 local identique au registre |
| 2026 | 54 | `F2026054.pdf` | 31 | texte | Couverture locale « N° 54 »; SHA-256 local identique au registre |
| 2026 | 55 | `F2026055.pdf` | 47 | texte | Couverture locale « N° 55 »; SHA-256 local identique au registre |
| 2026 | 56 | `F2026056.pdf` | 28 | texte | Couverture locale « N° 56 »; SHA-256 local identique au registre |
| 2026 | 57 | `F2026057.pdf` | 24 | texte | Couverture locale « N° 57 »; SHA-256 local identique au registre |

Les numéros 52–57 et le nombre de pages ont été relus sur les fichiers locaux avec pypdf 7.1.1; le SHA-256 a été recalculé sur chaque PDF et correspond à celui du registre pour les 7 fichiers. Pour le n° 17, le PDF est une image scannée : le chemin officiel et le nom donnent le n° 17, mais le numéro imprimé sur la couverture doit encore être confirmé à l'œil. Le registre a été corrigé pour indiquer les 15 pages/scannées du n° 17 et les 24 pages/texte du n° 57.

## Limites du corpus

La version française de la loi 90-11 est le corpus structuré de cette étape. La version arabe est un scan et la collecte/OCR arabe n'est pas garantie. Les numéros de JO 1990 sont des scans; le contrôle visuel ou OCR doit être relié à une page source précise avant d'affirmer une exactitude de transcription.

Le recueil du ministère du Commerce reste exclu de la collecte automatique conformément à la consigne du projet.
