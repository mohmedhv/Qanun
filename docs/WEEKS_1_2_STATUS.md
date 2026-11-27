# Weeks 1 and 2 status audit

Reviewed against the project reports and checklists on 27 November 2026. “Done”
means the repository contains the stated output and the documented check exists;
it does not turn a machine check into independent human approval.

## Week 1

| Work | Status | Evidence and remaining scope |
|---|---|---|
| French law corpus and article split | Done technically | 158 numbered article records and 160 chunks are present. The 10-article manual sample compares against a secondary 29-page PDF, not every article against the official JO. |
| Retrieval baseline | Done as a baseline | BM25 and E5 results for the seven in-scope questions are recorded in `docs/retrieval_comparison.md`. Q08 and Q09 still need legal-reference review; Q10 is out of scope. |
| OCR measurement | Partial | Three pages have OCR/reference comparisons and CER/WER, but a second person has not reviewed the reference transcriptions and proposed corrections. The six strict header misses are documented; the metric is not an independent full-text check. |
| UpGrowth relevance filter | Not evaluated | The 30 candidate texts in `eval/filter_labels.csv` have no relevance labels, so precision/recall cannot be calculated. |
| Arabic corpus | Not complete | The located Arabic JO is a scan; no validated Arabic OCR or coverage claim is present. |
| Source collection approval | Pending | `docs/collection_rules.md` asks for teacher confirmation before automated bulk collection. No such confirmation is recorded. |

## Week 2

| Work | Status | Evidence and remaining scope |
|---|---|---|
| Amendment inventory and source links | Done in the project record | 79 operations are linked to official or published JO references. The Week 2 report records all 79 as source-checked; the Week 3 follow-up newly rechecked the 28 that were originally flagged. This is not a second-person review of all wordings. |
| P3 schema, APIs, relations, and validators | Done technically | The SQLite schema, reloadable loader, version API, hierarchy ranking and audit tools are present. The expanded seed now has 52 versions across 30 articles, including the new 1991, 1996 and 2017 histories. |
| P4 legal-reference review | Pending | `docs/p4_week_deliverable.md` still marks independent second-person checks for 20 references as pending. The Week 2 handoff also identifies Q008 as requiring correction and Q08/Q09 as needing review. |
| Revised Windows retrieval run | Pending | P4 must rerun E5 and hybrid retrieval on Windows after the candidate/cache changes in its revised package, then preserve the new results and environment details. |

## What still needs you or a teammate

1. Ask a second person to review the 19 reconstructed article wordings in
   `data/week3/full_wording_review.csv` against the listed JO pages, and record
   their name/date and any corrections. Also complete P4's 20-reference
   second-person check.
2. Have the P4 owner verify Q08/Q09 and resolve Q008 in the reference audit.
3. Rerun the revised E5/hybrid benchmark on Windows and save its actual output
   and runtime details; the old result does not verify the revised package.
4. Label the 30 UpGrowth texts before claiming filter precision or recall.
5. Ask the teacher whether automated bulk JO collection is permitted before
   starting any such collection.
6. Decide whether the team will obtain and validate an Arabic corpus. Until
   then, keep Arabic coverage stated as unavailable/unverified.
7. Review the SNMG lexical Concept seed and decide whether to add more topics;
   the current graph labels matches as unreviewed candidates.

Items 1–3 require a human reviewer or a Windows run by the project owner; an
assistant cannot truthfully supply that independent sign-off or claim the
student ran the benchmark. Items 4, 6 and 7 require project-scope decisions or
labels. The technical version reconstruction and graph export are complete in
the workspace and are documented in `docs/P3_WEEK3_DELIVERY.md`.
