# Data contract

The SQLite schema is defined in `src/common/schema.sql`.

## Tables

- `texts`: one record per legal text, keyed by `text_id`, with type, number, title, signing/publication dates, language, rank, source URL, and PDF path.
- `articles`: article versions linked to a text. `(text_id, article_number)` and `(valid_from, valid_to)` are indexed. `valid_to = NULL` means the version is currently in force. Version dates describe validity; `modified_by_text_id` identifies a modifying text where known.
- `relations`: directed relations between texts, optionally tied to an article number.

## Controlled values

Dates use ISO `YYYY-MM-DD`. Rank levels: `1 Constitution`, `2 law/ordinance`, `3 decree`, `4 order`, `5 circular`. Article status: `in_force` or `repealed`. Relation types: `modifies`, `repeals`, `applies`, or `adds`.

