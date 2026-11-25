# P4 week 2 — Integrated submission checklist

> Note du 25 novembre 2026 : ce compte rendu concerne un paquet antérieur. Le dépôt courant ne contient pas la base P3 ni son code de versions; voir `docs/P4_HANDOFF_P3_P5.md` pour l'état vérifié actuel.

## Verified in this integration workspace

- P4 + P3 test suite: **30 passed**.
- P2 structure validator: **passed** (158 original articles).
- P3 version validator: **passed** (11 texts, 89 relations, four tracked articles, six version rows, temporal boundaries and repeal behavior).
- P4/P3 BM25 smoke test: **passed**, including historical Article 73 wording switch and exclusion of repealed Articles 72 and 87 bis after repeal.
- P4's Windows baseline evaluation evidence is included: 20 questions, BM25/E5/Hybrid metrics and failure analysis. These are observed results from the earlier Windows experiment, not a newly rerun E5 benchmark on the temporal integration.

## P3/P4 date-aware search behavior

The P3 `get_version()` API and `data/db/qanun.db` are now bundled. Undated searches retain untracked P2 articles as provisional, replace tracked articles with current P3 wording, and omit articles currently repealed. Dated searches only search articles with an explicit P3 version valid at that date. Current P3 coverage is four articles, so historical search is not yet complete for all 158 articles. `version_verified` remains false pending independent legal review.

## Remaining legal/team sign-off

- P3 amendment inventory: 79 rows, 19 remain `needs_review`.
- P4 question references: primary mapping check documented for 20/20 against original 1990 Journal officiel; independent second-person sign-off is still **0/20**.
- P5 must run the actual Groq retrieval integration and citation/quote validation against this interface.

## Run from repository root

```powershell
python -m pip install -r requirements-search.txt
python -m pytest -q tests/test_search_p4.py tests/test_search_p4_integration.py tests/test_versions.py
python -m src.structuring.validate
python -m src.versions.validate_versions
$env:JURIDEAZOR_SEARCH_METHOD='bm25'
python -m src.search.smoke_test --bm25-only
python -m src.search.build_embeddings
python -m src.search.evaluate
python -m src.search.smoke_test
python scripts/package_submission.py
```

Do not run `python -m src.structuring.build_db` over this integrated DB without reapplying P3's version rows: that builder reconstructs the P2 structure database and does not recreate P3's version history. The P3 SQLite database is included in this handoff ZIP despite being git-ignored, because `get_version()` requires it at runtime.
