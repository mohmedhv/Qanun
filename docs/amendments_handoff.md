# Amendments of law 90-11: handoff from P2 to P3 (week 2)

Files (in `data/interim/`): `amendments.json` (complete) and `amendments.csv` (same, open it in Excel).
Produced by `python src/structuring/parse_amendments.py` from `evolution_blocks.json`. Re-run it any time, the result is identical.

## What one record contains
| field | meaning |
|---|---|
| target_article | article number as text: `42`, `12 bis`, `73-1` (new articles keep their own number) |
| action | `modify`, `complete` (adds paragraph(s)), `insert` (new article), `repeal`, `term_substitution` (a word is added/replaced, no full text) |
| modifying_text_* | type, number and id of the amending text, e.g. `ordonnance-96-21` |
| date_signed | signature date written in the text (Gregorian) |
| jo_number, jo_date | Journal officiel issue and its publication date |
| amending_article | the article of the amending text that gives the instruction (e.g. `Art. 6`) |
| new_content / new_paragraphs | the NEW text quoted in the amending text (empty for repeal and term_substitution) |
| partial | `true` when only a part is quoted (the quote contains "......" or "sans changement") |
| instruction | the sentence of the amending text, to verify by eye |
| needs_review, review_reasons | why the record is not certain |

## What this file does NOT give you (your job, P3)
1. **Entry into force date.** We give the signature date and the JO publication date, nothing else. `valid_from` must come from the official text (signature date and entry into force are not the same thing).
2. **The full text of a version when `partial = true`.** We never invent it. Build it from the previous version and the added paragraph, and check it in the official text.
3. **Verification.** The records come from an annotated copy of the law, not from the official JO. Check every record you use in the official text.

## Known doubts (all flagged `needs_review`)
- `87 bis` repeal: the nearest header found in the page is an application decree (15-107), so the repealing text is **uncertain**. Find the real text in the JO.
- `partial` records: 12, 13, 31, 54, 97, 143 bis, 146 bis.
- The list comes from the "Evolution" blocks of the page. It may not be exhaustive: it is a good start, not proof that no other amendment exists.
- New articles like `73-1`..`73-6`, `12 bis`, `52 bis` are not in the 158-article base. They need their own rows (data contract: number is TEXT).

## Articles with at least one amendment (candidates for version tracking)
Good candidates have a clear before/after: **42, 44, 73, 87, 93, 98, 100, 102, 114, 134, 140, 149** (one modification = two versions), and **73-4, 87 bis, 143 bis, 146 bis** (created, then modified or repealed: two events).

| article | events |
|---|---|
| 12 | complete by Ordonnance 96-21 (JO 43, 1996-07-10) [FLAG] |
| 12 bis | insert by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 13 | complete by Ordonnance 96-21 (JO 43, 1996-07-10) [FLAG] |
| 22 | repeal by Ordonnance 97-03 (JO 3, 1997-01-12) |
| 23 | repeal by Ordonnance 97-03 (JO 3, 1997-01-12) |
| 24 | repeal by Ordonnance 97-03 (JO 3, 1997-01-12) |
| 25 | repeal by Ordonnance 97-03 (JO 3, 1997-01-12) |
| 26 | repeal by Ordonnance 97-03 (JO 3, 1997-01-12) |
| 31 | complete by Ordonnance 96-21 (JO 43, 1996-07-10) [FLAG] |
| 42 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 44 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 52 bis | insert by Ordonnance 97-02 (JO 3, 1997-01-12) |
| 52 quater | insert by Ordonnance 97-02 (JO 3, 1997-01-12) |
| 52 ter | insert by Ordonnance 97-02 (JO 3, 1997-01-12) |
| 54 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) [FLAG] |
| 72 | repeal by Décret législatif 94-09 (JO 34, 1994-06-01) |
| 73 | modify by Loi 91-29 (JO 68, 1991-12-25) |
| 73-1 | insert by Loi 91-29 (JO 68, 1991-12-25) |
| 73-2 | insert by Loi 91-29 (JO 68, 1991-12-25) |
| 73-3 | insert by Loi 91-29 (JO 68, 1991-12-25) |
| 73-4 | insert by Loi 91-29 (JO 68, 1991-12-25); modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 73-5 | insert by Loi 91-29 (JO 68, 1991-12-25) |
| 73-6 | insert by Loi 91-29 (JO 68, 1991-12-25) |
| 87 | modify by Loi 14-10 (JO 78, 2014-12-31) |
| 87 bis | insert by Décret législatif 94-03 (JO 20, 1994-04-13); repeal by Décret exécutif 15-107 (JO 22, 2015-04-29) [FLAG] |
| 91 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 93 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 93 bis | insert by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 97 | complete by Ordonnance 96-21 (JO 43, 1996-07-10) [FLAG] |
| 98 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 100 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 102 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 114 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 134 | modify by Ordonnance 96-21 (JO 43, 1996-07-10) |
| 140 | modify by Ordonnance 15-01 (JO 40, 2015-07-23) |
| 143 bis | insert by Ordonnance 96-21 (JO 43, 1996-07-10); modify by Loi 17-11 (JO 76, 2017-12-28) [FLAG] |
| 146 bis | insert by Ordonnance 96-21 (JO 43, 1996-07-10); modify by Loi 17-11 (JO 76, 2017-12-28) [FLAG] |
| 149 | modify by Ordonnance 15-01 (JO 40, 2015-07-23) |

Term substitution only (the words "accord collectif" are added after "convention collective" by ordonnance 96-21, art. 18): articles 115, 116, 117, 118, 119, 121, 122, 123, 124, 126, 127, 128, 129, 130, 131, 132, 133. No full new text exists for them.
