# P4 handoff to P3 and P5 — integrated version-aware build

## P4 delivers

- `src/search/`: BM25, multilingual E5, article-level RRF, evaluation and `search(question, date=None, k=5)`.
- `src/versions/`: P3 version API integrated from the supplied P3 handoff.
- `data/db/qanun.db`: P3 SQLite database required at runtime (intentionally included in this handoff ZIP; it remains git-ignored).
- `data/processed/chunks.jsonl`: P2 corpus (160 chunks representing 158 original articles).
- `eval/questions.csv`: 20 evaluation questions; independent second-person verification is still pending.
- Windows baseline artifacts: `search_metrics.json`, `search_results.csv`, `failure_analysis.csv`.

## Date-aware behavior implemented

`search(question, date=None, k=5)` now calls P3 `get_version()` for the four tracked articles (72, 73, 87, 87 bis).

- **Undated search:** the 154 untracked P2 articles remain provisional. For P3-tracked articles, the latest/current P3 wording replaces the original P2 chunk. Articles repealed by today (72 and 87 bis) are omitted.
- **Dated search:** only articles with an explicit P3 version valid on the requested date are eligible. Untracked articles are excluded because P3 has not supplied their historical validity. This is deliberately conservative and means dated-search coverage is currently limited to the four tracked articles (and fewer after repeal dates).
- Historical wording is taken from `versions.content`, not copied from the original P2 chunk. Long version texts are split by paragraphs when paragraph metadata is available.
- `version_record_available=True` means a P3 version row was found. `version_verified=False` remains until the independent legal source review is completed. A passing software validator is not legal sign-off.
- E5 vectors for a temporal corpus are cached separately by the exact document fingerprint. First semantic/hybrid date search for a new temporal corpus may encode and save a new cache; install `requirements-search.txt` and allow model download.

## P5 result contract

Each result includes:

`cite_id`, `article_id`, `article_number`, `text_id`, `chunk_id`, `text`, `source_url`, `score`, `version_id`, `valid_from`, `valid_to`, `version_status`, `version_record_available`, `version_verified`, `modifying_text_id`, `repealing_text_id`, `method`.

`score` is method-specific (BM25, cosine similarity or RRF), not a calibrated confidence probability. P5 must validate every citation against the retrieved set and ensure any quoted passage appears in the returned `text`. P5 should not treat `version_verified=False` as legally certified wording.

## Remaining cross-team work

1. P2/P3 must independently verify all 20 `eval/questions.csv` references and record status; current `independent_second_check` values remain PENDING.
2. P3's amendment inventory has 79 entries, of which 19 remain `needs_review`; those entries must not be presented as fully verified.
3. P3 currently tracks four articles and six version rows. Full historical search across the whole 158-article corpus is not yet supported; expand version coverage only after official source verification.
4. P5 must run its actual Groq/retrieval integration against this interface and keep citation/quote checks.

## Tests executed for this integrated package

From repository root:

```powershell
python -m pytest -q tests/test_search_p4.py tests/test_search_p4_integration.py tests/test_versions.py
python -m src.structuring.validate
python -m src.versions.validate_versions
$env:JURIDEAZOR_SEARCH_METHOD='bm25'
python -m src.search.smoke_test
```

The integrated source package was checked with 29 automated tests, P2 validator and P3 validator. E5 model inference was not rerun in the packaging environment; on Windows run the semantic/hybrid smoke test after installing dependencies and building embeddings.
