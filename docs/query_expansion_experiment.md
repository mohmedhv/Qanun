# P4 Query Expansion Experiment

## Purpose
Test generic French legal terminology expansion without question IDs,
expected article IDs, or article-specific rules.

## Conditions
- Baseline BM25/E5/Hybrid use the original question.
- Expanded BM25 searches one concatenated query containing the original and
  generic alternatives.
- Expanded E5 searches each generated query and fuses the article rankings
  with RRF.
- Expanded Hybrid fuses expanded BM25 and expanded E5.

## Data separation
Use `dev` for inspecting failures and refining terminology. Treat `test` as
held out; do not tune the dictionary after inspecting test metrics.

## Safeguards
The original query remains first. Expansion does not delete negation terms.
No target article IDs or expected citations are injected. Existing teacher
evaluation scripts and outputs are not overwritten.

## Scope
The evaluator loads the P2 corpus through `load_documents()`. It does not
evaluate P3 temporal-version retrieval. Dated P3 search requires a separate
evaluation through the version-aware search API.

## Reporting
Report all gains and regressions. Do not claim improvement unless baseline
and experimental runs use the same corpus, model, question set, and metrics.
