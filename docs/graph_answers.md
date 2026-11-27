# Graph answers: "which text modified article X?" (P5, week 3)

`src/rag/graph_answer.py` answers questions about the history of an article of loi 90-11 **from the knowledge graph, with no LLM call**. The answer uses the imposed 4-part format.

```
python -m src.rag.graph_answer "Quel texte a modifié l'article 73 ?"
python -m pytest tests/test_graph_answers.py
```

## How it works
1. **Article:** read from the question ("article 73", "l’article 87 bis", "art. 73‑4" with any dash).
2. **Graph** (P2, Ikram, `data/graph/edges.csv` and `nodes.csv`): take the `modifies`, `repeals` and `adds` edges from a text to that article. Each gives the amending text, its article (`provision`), the date signed, the JO number and date, the source URL, and the edge status (`verifie_jo_officiel`, `regex_to_check`, …). Text-to-text `summary_link` edges are ignored.
3. **Versions** (P3, Mohcem, `src/versions/versions.py`): `list_versions` checks each event against P3's history.
   - `confirmed`: a version was created or repealed by that text.
   - `mismatch`: versions exist, but none comes from that text.
   - `not_tracked`: P3 has no versions for the article.

   `get_version` gives the state today (in force, or no version in force).
4. **Citations:** every cited (text, article, relation, provision) is checked by `eval.citation_verifier.verify_graph_citations` against the graph edges.
5. **Confidence:**
   - **élevé:** every edge is verified in the official JO and every version check is `confirmed`.
   - **moyen:** the article isn't tracked by P3.
   - **faible:** there's a mismatch or an unverified edge.
6. **Refusal:** "Je ne trouve pas de règle dans le corpus." when the question names no article, the article doesn't exist, or the graph has no such edge.

## Examples (all checked by tests)

| Question | Answer from the graph | Version check | Confidence |
|---|---|---|---|
| Quel texte a modifié l'article 73 ? | Loi 91-29, Art. 2 (signed 1991-12-21, JO n°68 of 1991-12-25) | confirmed; in force (v2 since 1991-12-27) | élevé |
| Qui a abrogé l’article 87 bis ? | Added by décret législatif 94-03, Art. 1er (1994); repealed by loi 14-10, Art. 90 (2014-12-30) | both confirmed; no version in force | élevé |
| Quel texte a modifié l'article 73‑4 ? | Added by loi 91-29, Art. 3 (1991); modified by ord. 96-21, Art. 9 (1996) | 96-21 confirmed; **91-29 mismatch** | faible |
| Quel texte a abrogé l'article 22 ? | Ord. 97-03, Art. 8 (1997-01-11) | not tracked by P3 | moyen |
| Quel texte a modifié l'article 999 ? | refusal | — | — |

## Found while building this (to raise)
- **73-4: graph and P3 disagree.** The graph (verified in the JO) says loi 91-29 Art. 3 created 73-4 in 1991. P3's only version of 73-4 starts on 1996-07-12 and comes from ord. 96-21. So P3 has no 1991–1996 version of 73-4. For **Mohcem** (and Ikram).
- **Only 7 articles have P3 versions**, so most graph answers will say "not tracked" (confidence moyen). Example: art. 22.

## Limits
- The graph only covers the collected texts; an article with no edge gets a refusal, not "never modified".
- The answer gives the history (which text, when). It doesn't quote the new wording, which needs P3's version text.
- Built on Ikram's `p2/week3-graph-build` (PR #11). If her CSV format changes, `load_graph()` must follow.
