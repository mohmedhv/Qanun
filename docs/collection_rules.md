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
