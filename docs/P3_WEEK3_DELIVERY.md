# P3 Week 3 — P3 delivery

**P3 owner:** FOUGHALI Housseine  
**Documentary review tool:** Codex

FOUGHALI Housseine confirms reviewing the 28 amendment references and six sampled graph edges. He reports 26 November 2026 as his review date.

Inspected on 27 November 2026. Base splitter `63c6900`; Ikram's new graph
`a621355`. Work is local: no GitHub push, merge or teammate message was sent.
Git fetch confirmed main at 250b577 and the graph branch at a621355. The separate
P5 extraction (2dc4bdc) and graph-answer (bde0bab) branches add P5 evaluation
and RAG work. This delivery targets the P2 graph integration branch.
Full project included for testing; do not upload its whole tree over a newer
team branch. See the changed-file list before integrating.

## Implemented and checked

- Ontology documented in `docs/ontology.md` and `src/graph/ontology.py`, aligned
  with the shared contract. Row 9 supplies the historical citation 87 bis → 87.
  For row 54, décret exécutif 15-59 art.1 supplies the implementing link to article 87.
- All 79 amendment operations retained. `amendments.json`, `amendments.csv` and
  the original 51-row `P3_Officially_Checked_Examples.csv` remain byte-identical.
  Eight source pages were corrected in the authoritative verification CSV: two from 1994 and six from 2017 (142, 143, 143 bis on p.45 and 150, 151, 152 on p.46),
  with field-level before/after values in `data/week3/corrections.csv`.
- A reproducible row ledger, parser comparisons and Gold annotation are under
  `data/week3/`. `python -m src.versions.week3_audit` runs the unchanged parser
  with temporary outputs; it cannot overwrite the P3 reference inventory.
- All **28 originally source-flagged operations were rechecked individually**
  against the relevant rendered official JO pages in this session. Per-row
  source, provision, page and status are in `data/week3/official_review.csv`.
  The received CSV already records 79 verified source references; these checks
  confirm 28 of them anew, rather than claiming 79 new checks or human sign-off.
- Added original wordings for articles **22–26**, from JO 17/1990 printed p.490
  (PDF page 4). Ordonnance 97-03 art.8 repeals them; art.9 delays effect two
  months after publication on 12 January 1997: **repeal 1997-03-12**, final valid
  day **1997-03-11**. Article 22's old 44-hour wording never returns as current.
- Corrected inherited **87 bis** start date: the 1 January 1994 clause belongs
  to the adjacent decree **94-04**, not **94-03**. The latter's art.2 only orders
  publication. Using the project's Alger clear-day convention, publication on
  13 April gives **1994-04-15**. The original nine other version rows remain
  unchanged; version_id 6 has this documented correction, and new IDs are 13–17.
- Correct official source pages: DL94-03 / 87 bis is **JO 20/1994 p.5**, not 3;
  DL94-09 art.35 / repeal of 72 is **JO 34/1994 p.6**, not 7. Old values and
  original statuses remain traceable in the correction log and base Git commit.
- Integrated database: **15 versions, 12 tracked articles**, 158 baseline articles,
  160 chunks, 11 texts, 89 relations and 79 verification rows. Existing schema
  retained; loader preserves separately evidenced original-wording statuses.
- Imported Ikram's graph builder and tests unchanged. Reviewed six sampled edges,
  two each of modifies/adds/repeals, against official pages: **6/6 operation
  matches**. CSVs regenerated with her builder: **225 nodes / 300 edges**.
  The two open graph-export findings are in `docs/P3_GRAPH_REVIEW.md`.

## Verification evidence and scope

Documents were opened individually, never collected in bulk. Read visually:
JO 3/1997 pp.5–7; JO 20/1994 p.5; JO 34/1994 p.6; JO 78/2014 p.32;
JO 40/2015 p.16; JO 76/2017 pp.44–46; original JO 17/1990 p.490.
Document hashes and pages are in `data/week3/source_evidence.json`.

New `valid_from=1990-04-27` values retain the project's Alger convention,
derived from publication on 25 April and one clear day, not signature. The
SGG guide, https://www.joradp.dz/TRV/F2024G02.pdf#page=6 (printed p.5), restates
Civil Code art.4. This is an explicit date calculation scoped to Alger; it is
not proof of JO receipt dates in every daïra. The Ministry's direct Code PDF
failed to load. New version and correction evidence is in
`data/version_seed/p3_week3_evidence.json`.

Source-operation review is distinct from full consolidated wording and from an
independent human signature. The **16 wording-review flags remain visible**.
Reading JO 40/2015 p.16 confirms that article 140 ends with the first fine.
The recidivism paragraph belongs to article 149 and appears there in the
project inventory. Both texts have been retained.
No effective date for the 2017 penalty amendments was inferred from “finances
pour 2018” or signature. Those penalty articles still have no P3 version rows.

## Reconcile the numbers

| Count | Meaning and evidence |
|---|---|
| 79 | Current authoritative operation rows linked individually to SQLite |
| 59 | Historical P2 output at bf8cd0e; immutable copy in data/week3/baselines/p2_59.json |
| 8 | needs_review flags in that historical 59-row parser snapshot |
| 71 | Actual unchanged parser output after Ikram's splitter fix |
| 19 | Historical P4 wording-review count; membership reconstructed from delivery notes as fourteen 2017 cases plus five 1996 cases; original flag snapshot missing |
| 28 | Original source flags in original_status; all 28 rechecked here with individual pages |
| 16 | Current full-wording review flags in the preserved 79-row JSON |
| 51 | Original Gold list: 36 official-JO + 15 published-JO-copy rows |

These totals measure different snapshots/scopes and must not be added together.
`reference_reconciliation.csv` has exactly 79 rows and one current source status
per operation. Historical membership flags are separate and labelled.

The 59→79 difference consists of twelve 2017 targets (141–148, 150–152, 154)
and eight 2022 operations. The 71→79 difference is the eight loi-22-16 operations.
Both parser snapshots misattribute the 87 bis repeal to decree 15-107; P3 keeps
loi-14-10. Wording and flag changes are listed separately from missing rows.
No duplicate reference keys and no deleted operations were found.

The documented historical 19 becomes today's 16 through clearing 141/144/145
and the reconstructed article 12 version, while flagging incomplete 1991 wording
of 73-4. This is documentary reconstruction, not recovery of the original JSON.

## Gold and extraction score

All 51 original examples are retained in `gold_51.csv`, with source pages,
original Gold status, expected recoverability and current parser results.
**43** have their amending-text header in the actual input; **eight 2022**
operations have no source header there. Eligibility is based on input coverage,
not on whether the parser passed.

| Evaluation scope | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Original Gold 51 | 43 | 0 | 8 | 100% | 84.31% |
| Recoverable Gold 43 | 43 | 0 | 0 | 100% | 100% |
| All 79 operations | 70 | 1 | 9 | 98.59% | 88.61% |

Predictions for the Gold slice are restricted to its eligible legal texts.
Scoring uses (legal text, target, amending provision, action); duplicate
predictions count as false positives. It measures operation extraction, not
complete wording, general legal accuracy or independent graph verification.

## Execution and tests

```sh
python -m src.versions.week3_audit
python -m src.versions.rebuild_db
python -m src.graph.build_graph
python -m src.structuring.validate
python -m src.versions.validate_versions
python -m src.structure.validate_articles --text loi-90-11 --expect 158
python -m pytest -q
```

Full suite: **59 passed**, Linux, 27 November 2026, including Ikram's three graph
tests. All three validators pass; SQLite integrity and foreign-key checks pass.
New tests cover delayed repeals and boundaries, preservation of the 79-row input,
duplicate/wrong-attribution scoring, evidence pages and ontology endpoint checks.

P4 API signatures and search implementation remain unchanged. One search test
previously expected repealed article 22 as current; it now checks a historical
date and excludes it today. The 87 bis date regression now rejects dates before
15 April 1994. No test was disabled or removed.

Do not run the parser at default output paths over the reviewed 79-row JSON:
it writes 71 raw records and reintroduces the wrong 87 bis attribution.

## Remaining requirements and what to obtain

1. **Original snapshot underlying the historical 19 flags**, if P4 still has it.
   Existing docs prove the count, while row membership is reconstructed.
2. **Ikram's follow-up graph fix:** versions 6, 11 and 12 lack belongs_to edges;
   the export omits validity/repeal fields and writes valid_from into date_signed.
   Her algorithm was not rewritten by P3. See P3_GRAPH_REVIEW.md for the message.
3. **Human sign-off / full-wording review:** the owner confirmed the 28 reference and six edge checks;
   the 16 existing wording-review flags remain. No new files are needed merely
   to access the official sources already listed in the project.

| Requirement | Status |
|---|---|
| Ontology in requested files | COMPLETED — project vocabulary, directions and documented examples |
| Count ledger / Gold / parser scoring | COMPLETED for inspected snapshots; original 19-membership evidence pending |
| Additional official verification | COMPLETED — 28/28 rechecked, page references recorded; 0 pending for these source-operation checks |
| Verified version extension / integrated database | COMPLETED — five additions and one evidenced date correction |
| Sample of Ikram's graph edges | COMPLETED — six documentary checks; export defects reported separately |
| Tests and validators | COMPLETED — 59 tests, three validators, SQLite checks |
| Temporal completeness of graph CSV | PARTIALLY COMPLETED — two fixes needed from graph owner |
| Remaining consolidated wording and human sign-off | NOT COMPLETED — 16 wording flags remain outside the confirmed reference and edge checks |

Test runtime: Python 3.12.14, pytest 8.3.3, NetworkX 3.3 (project pin). Linux full suite: 59 passed. Windows was not tested in this run.
