# Chunking strategy (P2 -> P4), week 2

## Decision
**One article = one chunk.** An article longer than 1500 characters is split **by paragraph**, never in the middle of a paragraph, and **every part keeps the article id** (`loi-90-11-art-94#1`, `loi-90-11-art-94#2`; the `article_id` column is always `loi-90-11-art-94`). A citation therefore always points to the right article.

## Why (numbers measured on the 158 articles of law 90-11)
| measure | value |
|---|---|
| shortest article | 55 characters |
| median | 269 characters |
| 90% of articles are shorter than | 801 characters |
| longest article (no. 94) | 2216 characters |
| articles above 1500 characters | 2 (no. 7 and no. 94) |

1. **The article is the unit we must cite.** A chunk that equals an article makes the citation check trivial (the cited id must be in the retrieved set).
2. **It fits the embedding models.** E5 multilingual and BGE-M3 read at most 512 tokens (about 1800-2000 French characters). The limit of 1500 characters leaves room for the "passage:" prefix and the context line.
3. **It keeps LLM calls small.** The shared model has about 8000 tokens per minute: short chunks keep each call well under 4000 tokens.
4. **Splitting by fixed size would cut sentences and lists.** Splitting by paragraph keeps each item of a list whole.

## Details
- When the first paragraph ends with ":" (an intro such as "...les obligations suivantes :"), it is **repeated at the top of the following parts**, so a list item is never read without its intro.
- **`text_for_embedding`** = `Loi n° 90-11, article N (TITRE ... > Chapitre ... > Section ...)` + the text. P4 embeds this field (the article number and its place in the law help the search), and shows `text` to the user and the LLM.
- Result: **160 chunks for 158 articles** (articles 7 and 94 give 2 chunks each; longest chunk = 1391 characters). Checked by script: no paragraph is lost.

## How P4 uses it
Table `chunks` in `data/db/qanun.db` (columns: chunk_id, article_id, part, n_parts, text, text_for_embedding, n_chars, source_url) and the same data in `data/interim/chunks.json`. Build with `python src/structuring/build_db.py` then `python src/structuring/chunks.py` (the second step needs the first).

## Open points
- **Versions (P3):** when an article has several versions, each version should be chunked with the same rule and keep `article_id` + a version id. To agree with P3 and P4.
- **Arabic:** if the Arabic edition is indexed, each Arabic article is its own chunk, linked to the French one by the same article number (to agree with the team, see `docs/noisy_test.md`).
- The 1500-character limit is a starting value. P4 can change `MAX_CHARS` in `chunks.py` if the retrieval tests suggest it.
