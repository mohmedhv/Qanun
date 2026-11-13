# Data contract - PROPOSAL from P2 (to be confirmed by P1, P3, P4, P5)

Status: draft, written from the working code in `src/structuring/build_db.py`.
Database file: `data/db/qanun.db` (SQLite). Rebuilt from scratch by `python src/structuring/build_db.py`.
If this file differs from an existing `data_contract.md`, the existing one wins and P2 renames columns.

## Conventions
- Dates: ISO text `YYYY-MM-DD`. `valid_from` is the ENTRY INTO FORCE date, not the signature date. P3 fills it.
- IDs: `article_id = <text_id>-art-<number>`, number with spaces replaced by `-`. Example: `loi-90-11-art-33`, `loi-90-11-art-12-bis`.
- Article numbers are TEXT (`"33"`, `"12 bis"`). `sort_key` is the integer part, used for ordering.
- Modified or repealed articles keep their number. Never delete a row: use `status`.
- `status` values: `in_force`, `repealed`.

## Table `texts`
| column | type | meaning |
|---|---|---|
| text_id | TEXT PK | `loi-90-11` |
| type | TEXT | loi / ordonnance / decret / arrete / circulaire |
| number | TEXT | `90-11` |
| title | TEXT | full title |
| date_signed | TEXT | signature date |
| jo_number | TEXT | Journal officiel issue, e.g. `JO n°17` |
| jo_date | TEXT | JO publication date |
| source_url | TEXT | official URL (JORADP) |

## Table `articles`
| column | type | meaning |
|---|---|---|
| article_id | TEXT PK | see conventions |
| text_id | TEXT FK -> texts | parent text |
| number | TEXT | `"33"` or `"12 bis"` |
| sort_key | INTEGER | 33 |
| suffix | TEXT | NULL / bis / ter |
| parent_title | TEXT | e.g. `TITRE III : RELATIONS INDIVIDUELLES DE TRAVAIL` |
| parent_chapter | TEXT | e.g. `Chapitre IV : ...` (may be NULL) |
| parent_section | TEXT | e.g. `Section 1 : ...` (may be NULL) |
| content | TEXT | full article text (paragraphs joined by newline) |
| paragraphs | TEXT | JSON list of alineas |
| status | TEXT | default `in_force` |
| valid_from | TEXT | filled by P3 |
| valid_to | TEXT | NULL for the current version |
| source_url | TEXT | provenance link |

Unique constraint: (`text_id`, `number`).

## Table `relations`
| column | type | meaning |
|---|---|---|
| relation_id | INTEGER PK | auto |
| source_id | TEXT | text_id or article_id |
| target_id | TEXT | text_id or article_id |
| type | TEXT | modifies / repeals / applies / cites |

## Versions (P3)
A `versions` table is NOT defined here yet. P3 proposes it (article_id, version_no, content, valid_from, valid_to, modifying_text_id).

## Chunking (P4)
One article = one chunk, identified by `article_id`. Very long articles may be split by paragraph but keep `article_id`. Longest article is #94 (about 2200 characters).

## Questions to confirm
1. P1: is there an existing `data_contract.md` with different names?
2. P3: do you want `versions` as a separate table or as extra rows in `articles`?
3. P4/P5: are `article_id` and the column names above fine for your code?
