# P3 review of Ikram's Week 3 graph

## Follow-up on main — 27 November 2026

The findings below describe the first P3 export. The follow-up graph builder now
adds exactly one `belongs_to` edge for every Version, checks that invariant, and
exports `version_id`, `article_id`, `content`, `valid_from`, `valid_to`,
`repeal_date` and verification metadata. It also creates a small lexical
`concept:snmg` candidate with `mentions` edges marked
`lexical_match_unreviewed`. The regenerated graph has 226 nodes and 308 edges,
including all 15 Version ownership edges and five lexical mention edges. The
focused graph tests pass (8/8). The six-edge documentary sample remains the
same; full wording review and human concept-vocabulary review are still open.

The original graph implementation and CSV counts below are preserved as the
historical inspection record, not as the current export status.

**P3 owner:** FOUGHALI Housseine  
**Documentary review tool:** Codex

FOUGHALI Housseine confirms reviewing the six sampled graph edges. He reports 26 November 2026 as his review date.

Inspected branch `p2/week3-graph-build`, commit
`a6213554c75aea09b169427e3652fe579f12bfc3` on 27 November 2026.
P3 imported the published builder, graph tests and contract unchanged. No remote
push/merge occurred. Graph algorithms remain Ikram's work.

The graph reads SQLite and creates CSVs without modifying database tables.
Its amendment directions and canonical IDs match P3. Original branch export:
220 nodes / 295 edges. Regenerating with P3's five additional versions produces
225 nodes / 300 edges. The extra five ownership edges belong to versions 13–17.

## Documentary sample

| Relation | Source → target | Official evidence | Result |
|---|---|---|---|
| modifies | loi-17-11 → 141 | JO 76/2017 p.44, art.99 | Match |
| modifies | loi-17-11 → 144 | JO 76/2017 p.45, art.99 | Match |
| adds | ordonnance-97-02 → 52 bis | JO 3/1997 p.6, art.2; heading p.5 | Match |
| adds | ordonnance-97-02 → 52 ter | JO 3/1997 p.6, art.3; heading p.5 | Match |
| repeals | ordonnance-97-03 → 22 | JO 3/1997 p.7, arts.8–9 | Match; effect 1997-03-12 |
| repeals | ordonnance-97-03 → 26 | JO 3/1997 p.7, arts.8–9 | Match; effect 1997-03-12 |

Individual links, pages and review scope are in `data/week3/graph_edge_review.csv`.
This is Codex documentary checking, not a claimed independent human signature
or exhaustive verification of every graph edge.

## Findings from the original export

1. **Three missing ownership edges:** `version:6`, `version:11`, `version:12`
   have no outgoing `belongs_to`. Their Articles (87 bis, 12 bis, 73-4) are
   created later in the relation loop, after the Version loop's membership check.
   The builder's existing `check()` does not detect this omission.
2. **Temporal fields lost in CSV:** Version nodes put `valid_from` in
   `date_signed`; the export omits `valid_from`, `valid_to`, `repeal_date`,
   `verification_status`, `article_id` and `content`. Preserve temporal metadata
   if CSV consumers need it; otherwise consumers must use the P3 SQLite/API.
   Do not select current wording from the graph node's `date_signed` field.
3. The ontology records Concept as a legal topic. The builder exports Text,
   Article and Version. The decree 15-59 → article 87 edge is supported by art.1,
   JO 8/2015 p.11. The graph's portal-derived status is retained. See
   [ontology.md](ontology.md) for evidence. Other candidate edges retain their
   existing review status.

At the original inspection, the builder integrity check and three graph tests
passed as part of the **59-test** full suite. Those checks did not certify
temporal CSV completeness; the two findings above were then open.

Historical suggested handoff (the export fixes above have since been applied):

> I checked a621355. Six sampled modifies/adds/repeals edges match the official
> JO. All 59 combined tests pass. Please add the missing belongs_to edges for
> version:6, version:11 and version:12: their Article nodes are created after the
> Version loop. Also keep valid_from/valid_to and repeal_date in the Version
> export; valid_from is currently written as date_signed. P3 now has 15 versions,
> so regenerating your CSVs produces 225 nodes and 300 edges. I also corrected
> two inherited 1994 source pages and the 87 bis start date after checking the JO;
> details are in data/week3/corrections.csv. The 79 operation records are retained.
