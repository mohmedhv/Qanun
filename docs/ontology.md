# P3 Week 3 ontology

Base: splitter `63c6900`; Ikram's `p2/week3-graph-build`, commit `a621355`
(27 November 2026 inspection). Endpoint directions follow her new graph contract.
The vocabulary follows the shared data contract and the 79-row P3 reference list.
Current graph construction and export are implemented in `src/graph/build_graph.py`.

## Entities

| Entity | Meaning / identifier | Example traceable to the 79-row inventory |
|---|---|---|
| Text | Legal instrument, existing `texts.text_id` | `loi-91-29`, inventory row 1 |
| Article | Stable legal provision, `<text_id>-art-<number>` | `loi-90-11-art-73`, row 1 |
| Version | Wording and validity interval; existing integer `versions.version_id` | version 2 of article 73, database version_id 2, row 1 |
| Concept | Descriptive legal topic; no existing SQLite Concept table | “salaire national minimum garanti (SNMG)”, article 87, row 54. Label observed in wording, not a pre-existing graph node or verified taxonomy. |

Graph prefixes (`text:`, `article:`, `version:`) belong to export identifiers;
they must not replace database IDs. A Version node must retain `version_id`,
`article_id`, `content`, `valid_from`, `valid_to`, `status`, `repeal_date`,
`source_url` and `verification_status`. Retrieve wording through
`src.versions.versions.get_version(text_id, article_number, date=None)`;
`list_versions(text_id, article_number)` returns the complete available history.
No missing historical wording should be created from a partial amendment.

## Relations

| Relation | Direction and meaning | Evidence/example |
|---|---|---|
| belongs_to | Article → Text; Version → Article | article 73 → `loi-90-11`, ownership derived from row 1; version 2 → article 73. Matches Ikram's a621355 contract. |
| modifies | Amending Text → affected Article; source Article → target Article only when source provision is represented explicitly | `loi-91-29` → article 73, row 1, JO 68/1991 p.2167, art.2 |
| adds | Amending Text → new Article | `loi-91-29` → article 73-1, row 2, JO 68/1991 p.2167, art.3 |
| repeals | Repealing Text → affected Article | `ordonnance-97-03` → article 22, row 49; art.8, JO 3/1997 p.7; effect delayed by art.9 |
| applies | Application Text → implemented Article | Row 54 modifies article 87 and provides for a decree on the SNMG. Article 1 of décret exécutif 15-59 explicitly implements that provision. The decree is supplementary evidence for this existing graph edge. [JO 8/2015, p.11](https://www.joradp.dz/FTP/jo-francais/2015/F2015008.pdf#page=11) |
| cites | Citing Text/Article → cited Text/Article | The wording of 87 bis in insertion row 9 explicitly refers to article 87. The citation is historical and belongs to the inserted wording. [JO 20/1994, p.5](https://www.joradp.dz/FTP/Jo-Francais/1994/F1994020.pdf#page=5) |
| mentions | Article/Version → Concept | A literal vocabulary match links wording that names a candidate topic; this edge is lexical evidence, not a legal classification. |

Existing SQLite relations also contain ten Text → Text `modifies` summaries.
Do not count those ten as additional amendment rows. Keep the provision (`Art. 2`,
etc.) and source CSV row as edge evidence when exporting.

Inventory actions map as follows: `modify`, `complete`, `term_substitution` →
`modifies`; `insert` → `adds`; `repeal` → `repeals`.
An added paragraph (`complete`) does not create an Article node.

`src/graph/ontology.py` preserves ENTITIES and RELATIONS and exposes
`relation_for_action` and `validate_edge`. Endpoint validation does not certify
legal accuracy. No Graph implementation or separate CSV graph format is imposed.

The builder creates typed Article and Version nodes from the integrated database.
It also exports explicit `version_id`, `article_id`, `content`, validity and
repeal fields. A small seeded lexical vocabulary currently recognizes the
documented “salaire national minimum garanti” / “SNMG” wording as `concept:snmg`.
Matching Article and Version nodes point to that Concept with `mentions` edges
marked `lexical_match_unreviewed`. This is a starter extraction, not a complete
legal-topic taxonomy; a human should review the seed and add other concepts.
The independent six-edge sample is recorded in `data/week3/graph_edge_review.csv`.

## Evidence rules

One operation key is `(modifying_text_id, target_article, amending_article)`.
One current source status is copied from the authoritative P3 CSV; `needs_review`
is a separate wording flag. Original source status, parser flags, and historical
counts must not overwrite that current status. A checked edge needs an official
link, printed page, source provision, target and operation. A human sign-off is
distinct from this Codex documentary review.
