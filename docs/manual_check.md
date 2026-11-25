# Manual check - 10 articles of law 90-11

**Source file checked:** `loi_90-11_relations_de_travail.pdf` (29 pages), the PDF from which `data/raw/loi_90_11.txt` was extracted.
**What this check proves:** that the splitter and the database reproduce this PDF (number, text, headings, paragraphs).
**What it does NOT prove:** that this PDF is identical to the official Journal officiel. That second check is a different sheet (`docs/manual_check_official.md`, to do).
Page numbers below are the pages of the 29-page PDF above (not the page numbers of the Journal officiel).

| Article | PDF page | Text OK? | Heading OK? | Paragraphs OK? | Note |
|---|---|---|---|---|---|
| 1 | 1 | OK | OK | OK | |
| 4 | 1-2 | OK | OK | OK | page number "2" in the source was removed |
| 18 | 5 | OK | OK | OK | source says "dix (06) mois", kept as is |
| 33 | 7 | OK | OK | OK | |
| 41 | 7 | OK | OK | OK | |
| 54 | 9 | OK | OK | OK | |
| 72 | 11 | OK | OK | OK | |
| 73 | 12 | OK | OK | OK | |
| 99 | 18-19 | OK | OK | OK | article continues on page 19 |
| 158 | 29 | OK | OK | OK | |

Error rate on the sample: 0/10

## Six en-têtes manqués par la règle stricte — repères dans le JO officiel

Le numéro de page du Journal officiel correspond à la page PDF + 486. Ces lectures consignent les repères du scan; une relecture humaine indépendante reste nécessaire avant de les traiter comme référence OCR validée.

| Article | Lecture OCR | En-tête lu sur le scan | Page PDF | Page JO | Colonne |
|---:|---|---|---:|---:|---|
| 1 | `Article 1er.` (non reconnu par la règle stricte limitée à `Art.`) | `Article 1er. —` | 2 | 488 | droite |
| 30 | `Ârt. 30.` | `Art. 30.` | 5 | 491 | gauche |
| 54 | `Art. 54;` | `Art. 54.` | 6 | 492 | gauche |
| 82 | `Art. 82:+-` | `Art. 82.` | 9 | 495 | gauche |
| 144 | `Art ra —` | `Art. 144. —` | 14 | 500 | gauche |
| 146 | `Art. 148.` | `Art. 146.` | 14 | 500 | gauche |

L'article 1 est correctement imprimé « Article 1er »; il s'agit d'une limite du motif du vérificateur, pas d'une erreur OCR. À la page PDF 14, l'OCR lit 148 à la place de 146, tandis que le véritable article 148 apparaît plus loin. Ce tableau d'en-têtes ne vérifie pas le texte intégral des 158 articles par rapport au Journal officiel.

| 12 | portal copy: "prestations" | official JO (PDF p.3 / JO 489, right column): "prestation" | one-letter difference, base kept unchanged, to decide with P1/P3 |

| 2 | portal copy: dénommée » employeur « . | official JO (PDF p.2 / JO 488, right column): dénommée “ employeur ”. | quote marks only, words identical, base kept unchanged |