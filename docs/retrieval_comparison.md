# Retrieval comparison: Law 90-11

Generated: 2026-11-23

## Corpus and method

- Corpus: 158 chunks, one per article in data/interim/articles.json; article numbers 1–158, with no number gaps.
- The workspace has no built SQLite database in data/db; this run uses the current JSON article base. Confirm it matches Ikram's latest shared database before submission.
- Questions: all 10 rows in eval/questions.csv. The relevance references are the article numbers supplied in that file.
- BM25: standard Okapi BM25 (k1=1.5, b=0.75), Unicode accent normalization and word tokens, top 3.
- Dense retrieval: sentence-transformers is not installed in this environment.
- Hit@3 is yes if at least one reference article appears in the top 3. P@3 divides the relevant hits by 3; R@3 divides by the number of reference articles.
- Aggregate metrics include only the 7 in-scope questions whose reference labels are marked verified=oui. Q08 and Q09 remain visible but are excluded because their labels are unverified; Q10 is out of scope.

## Per-question results

| ID | Refs | Label | BM25 top 3 | Hit@3 | P@3 | R@3 | Embedding top 3 | Hit@3 | P@3 | R@3 |
|---|---|---|---|---:|---:|---:|---|---:|---:|---:|
| Q01 | 8, 9 | oui | 10, 12, 13 | no | 0/3 | 0/2 | pending | n/a | n/a | n/a |
| Q02 | 12, 13 | oui | 15, 31, 12 | yes | 1/3 | 1/2 | pending | n/a | n/a | n/a |
| Q03 | 18 | oui | 19, 18, 20 | yes | 1/3 | 1/1 | pending | n/a | n/a | n/a |
| Q04 | 22, 24 | oui | 22, 66, 47 | yes | 1/3 | 1/2 | pending | n/a | n/a | n/a |
| Q05 | 39, 40, 41, 42 | oui | 157, 64, 94 | no | 0/3 | 0/4 | pending | n/a | n/a | n/a |
| Q06 | 31, 32 | oui | 31, 32, 106 | yes | 2/3 | 2/2 | pending | n/a | n/a | n/a |
| Q07 | 73, 74 | oui | 82, 81, 89 | no | 0/3 | 0/2 | pending | n/a | n/a | n/a |
| Q08 | 73, 74, 75 | a_verifier | 41, 81, 148 | no | 0/3 | 0/3 | pending | n/a | n/a | n/a |
| Q09 | 12, 13 | a_verifier | 89, 77, 27 | no | 0/3 | 0/2 | pending | n/a | n/a | n/a |
| Q10 |  | non_concerne | 68, 20, 66 | n/a | n/a | n/a | pending | n/a | n/a | n/a |

## Aggregate on verified, in-scope questions

| Method | Hit@3 | Mean P@3 | Mean R@3 |
|---|---:|---:|---:|
| BM25 | 4/7 (57.1%) | 0.238 | 0.429 |
| Embeddings | n/a | n/a | n/a |

## Status and next step

A pending embedding result is not a zero score. Install the pinned sentence-transformers dependency and cache the model approved for the project, then rerun this script. It uses local model files only and does not download weights or call an LLM.

This is article retrieval evaluation, separate from the UpGrowth issue-filter evaluation. The 30 rows in eval/filter_labels.csv currently have no relevance labels, so precision and recall for the issue filter cannot yet be calculated.
