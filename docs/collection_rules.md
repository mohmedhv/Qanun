# Collection rules (Qanun)

Fill the blanks after reading the sources yourself. Do not copy from memory.

## Sources used
| Source | Used for | License / conditions | Checked on |
|---|---|---|---|
| Upgrowth JORADP index (CSV), https://www.upgrowth.dz/datasets/journal-officiel-1962-2026 | List of issues and PDF links | CC BY 4.0 (the index only, not the state's PDFs). Cite: UpGrowth (2026), Index du Journal officiel algérien. | 2026-11-__ |
| JORADP (joradp.dz) | Official PDFs, French and Arabic editions | Terms of use: ______________________ | 2026-11-__ |

## robots.txt of joradp.dz
- Opened at: https://www.joradp.dz/robots.txt (date: ______)
- Content summary: ______________________ (paste the relevant lines)
- Is automatic download of `/FTP/` allowed? [ ] yes  [ ] no  [ ] unclear -> if unclear or no, ask the teacher and use the fallback corpus.

## Our crawler behaviour
- Delay between requests: 3 seconds or more.
- Identifies itself with a User-Agent (see `src/collect/downloader.py`).
- Checks robots.txt before downloading and refuses if disallowed.
- Registry file `data/processed/download_registry.csv`: one line per PDF (URL, hash, date); a second run downloads nothing again.
- Only a few issues are downloaded for the week-1 demo.

## Not to be scraped
- The recueil de textes of the Ministry of Commerce website (its robots.txt forbids automatic access).

## Issues downloaded in week 1
| Year | Number | Edition | Pages | Text or scan | Why this issue |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Source of data/raw/loi_90_11.txt (added by P2)

- Law: Loi n° 90-11 du 21 avril 1990 relative aux relations de travail (JORA n° 17, 25/04/1990)
- Page given by the person who retrieved the file (P2's friend): https://www.mtess.gov.dz/fr/loi-n-90-11-du-21-avril-1990-relative-aux-relations-de-travail-page-488-rectificatif/
  (site of the Ministry of Labour, MTESS; URL reported by the friend, not opened by the team)
- Retrieved by: P2's friend, manually (no scraping). Date of retrieval: 2026-11-08
- File used: loi_90-11_relations_de_travail.pdf (29 pages, annotated portal copy, French)
- Licence / terms of use: not checked (TO CONFIRM). It is a public legal text; the MTESS terms were not read.
- The friend said he "translated" it into French. Our check shows it is not a free translation:
  compared with the official French JO scan (F1990017_1.pdf, read by OCR), 45 of the 97 articles
  we could compare are word-for-word identical, median difference 1.2% (the rest is OCR noise).
  61 articles were not compared because the OCR splitting failed on them.
- Limits: the copy is a consolidated version with "Évolution" notes, so some articles may differ
  from the 1990 original. Not yet checked article by article against the official scan.