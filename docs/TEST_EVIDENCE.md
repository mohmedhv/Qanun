État P3 Week 2 au 26 novembre 2026: module, base et chargeur intégrés. Résultats courants dans docs/P3_WEEK2_DELIVERY.md. Les observations antérieures ci-dessous sont historiques.

# Integrated P2/P3/P4 test evidence

> Note du 25 novembre 2026 : ce document décrit une distribution antérieure. Le dépôt courant ne contient pas la base P3, `src/versions/versions.py` ni le validateur P3; ces résultats historiques ne remplacent pas les vérifications courantes consignées dans le relais et les questions ouvertes.

## Checks executed in the integration workspace

The P3 database and version module supplied in `Qanun (1).zip` were merged with the reviewed P4 search package. The following checks were executed after integration:

- `python -m pytest -q tests/test_search_p4.py tests/test_search_p4_integration.py tests/test_versions.py`: **30 passed**. This includes P3's 11 version/hierarchy tests, P4 BM25 and search tests, historical version switching, inclusive validity boundaries, repeal exclusion, and a mocked Hybrid temporal-index test.
- `python -m src.structuring.validate`: **ALL CHECKS PASSED** (158 original articles, no missing/duplicate numbers or empty articles).
- `python -m src.versions.validate_versions`: **ALL CHECKS PASSED** (11 texts, 89 relations, 4 tracked articles, 6 version rows, valid date boundaries, repealed articles not current, amendment JSON/CSV synchronized).
- `JURIDEAZOR_SEARCH_METHOD=bm25 python -m src.search.smoke_test --bm25-only`: **P4/P3 API smoke test PASSED**, including Article 73 historical wording switch and repeal exclusion.

## E5 / Hybrid runtime status

The packaging workspace does not have `sentence-transformers` installed and does not include model weights or `.npz` caches. Therefore E5/Hybrid inference on the newly assembled temporal corpus was **not rerun here**. The previously observed Windows baseline metrics remain included as historical experiment evidence; they are not claimed as a fresh evaluation of the newly integrated temporal corpus. On Windows, install `requirements-search.txt`, run `python -m src.search.build_embeddings`, then run `python -m src.search.evaluate` for the original static benchmark and `python -m src.search.smoke_test` to test BM25, E5, Hybrid and P3 date-aware search. The first date-scoped semantic/hybrid search may build a separate cache for that exact temporal corpus.

## Legal verification status

- P3 validator reports 79 amendment inventory rows, **19 still marked `needs_review`**. Do not describe all amendment wording as fully verified.
- The 20 P4 question-to-article references have primary mapping notes against the original 1990 issue, but **independent second-person verification remains 0/20 and PENDING** in `eval/questions.csv`.
- P3 currently tracks four articles (72, 73, 87, 87 bis) in six version rows. Dated search is therefore conservative and limited to those tracked articles; untracked articles are not asserted as historically valid.

## Scope of passing tests

Passing tests establish software behavior against the supplied database and test fixtures. They do not constitute legal advice, independent official-source certification, or proof that all 158 articles have complete current/historical wording.
