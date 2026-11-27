# LLM alone vs RAG on the first 10 questions (P5)

Both runs use **`openai/gpt-oss-120b`** via Groq (teacher-imposed model), through the cache, and are hand-scored by Maram. No Gemini result is used.

| | LLM alone | RAG |
|---|---|---|
| Run | 2026-11-26, 10 calls | 2026-11-27, 10 calls |
| Prompt | Question only; Q01–Q09 prefixed "En droit algérien, " | System prompt (`prompts/system_prompt.txt`) plus the 5 articles from P4 `search()` (hybrid BM25+E5, undated) |
| Data | `eval/baseline_llm_alone.csv` | `eval/rag_answers.csv` |
| Reproduce (from cache) | `python -m eval.baseline_llm_alone` | `python -m eval.rag_pipeline --batch` |

Rerunning either script rewrites its CSV and empties the hand-score columns, so keep a copy first.

## Per question

| Q | Level | Expected art. | LLM alone | LLM error | RAG retrieved | RAG cited | RAG | RAG error |
|---|---|---|---|---|---|---|---|---|
| Q01 | directe | 8, 9 | partial | invented_article | 10, 8, 63, 11, 13 | 8, 10 | **yes** | — |
| Q02 | directe | 12, 13 | partial | invented_article | 47, 12 bis, 120, 73, 139 | 12 bis (names 12) | no | retrieval_error |
| Q03 | directe | 18 | no | invented_article + wrong_figure | 18, 19, 20, 43, 44 | 18, 19, 20 | **yes** | — |
| Q04 | directe | 22, 24 | partial | invented_article + no_version | 22, 33, 24, 23, 43 | 22 | no | wrong_version |
| Q05 | directe | 39–42 | partial | invented_article | 157, 64, 94, 41, 40 | 40, 41 | partial | retrieval_error |
| Q06 | combinée | 31, 32 | no | invented_article + wrong_figure | 31, 32, 36, 106, 89 | 31, 32 | **yes** | — |
| Q07 | combinée | 73, 74 | no | foreign_law + invented_article | 77, 62, 27, 82, 81 | 77 (refuses) | no | retrieval_error |
| Q08 | cas pratique | 73, 74, 75 | no | foreign_law + invented_article | 81, 41, 83, 73-4, 73 | 73, 73-4 | partial | wrong_quote |
| Q09 | datée | 12, 13 | no | wrong_version + invented_article | 27, 77, 62, 96, 97 | none (refuses) | no | retrieval_error |
| Q10 | hors périmètre | — (refuse) | no | out_of_scope_answered | 68, 20, 66, 120, 51 | none (refuses) | **yes** | — |

## Totals

| | LLM alone | RAG |
|---|---|---|
| Correct | 0 / 10 | **4 / 10** |
| Partly correct | 4 / 10 | 2 / 10 |
| Wrong | 6 / 10 | 4 / 10 |
| In-scope questions correct (Q01–Q09) | 0 / 9 | 3 / 9 |
| **Answers with invented sources** (non-existent text, or an article not provided) | **9 / 10** | **0 / 10** |
| Foreign law used | 2 / 10 | 0 / 10 |
| Wrong figure stated as law | 2 (overtime +25 %, trial 3 months) | 0 |
| Quote that misstates the article | — | 1 (Q08) |
| Out-of-scope question refused | 0 / 1 | **1 / 1** |
| In-scope question refused when retrieval failed ("Je ne trouve pas de règle dans le corpus") | — | 2 (Q07, Q09) |

**Invented sources, LLM alone:**
- non-existent texts: "Ordonnance 90-08 portant Code du travail", "Décret 85-11", "Ordonnance 66-03" as the 1997 code, "loi 19-07", "décret 13-03";
- court rulings and a book that can't be checked;
- wrong article numbers in every answer.

**RAG:** every article the model cited was in the 5 articles it received. Q02 names art. 12 only because the quoted art. 12 bis mentions it.

## What changes and why
- **Grounding works.** With the retrieved articles and the system prompt, the model stops inventing texts and numbers. Every RAG answer uses the 4-part format, and the right figures appear: +50 % overtime, 6/12-month trial period, 2.5 days per month of leave.
- **The main RAG error is now retrieval: 4 of the 6 answers not fully correct.** The other two are Q04 (wrong version) and Q08 (a quote that joins two paragraphs of 73-4 and misstates the condition). When the right article isn't in the top 5 (12 for CDD, 73 for dismissal, 42 for leave in the South), the model either refuses honestly (Q07, Q09) or says the context is insufficient (Q02). That's a much safer failure than the baseline's confident invention.
- **One version error (Q04).** Search flagged art. 22 as `historical_repeal_documented`, but the pipeline doesn't pass that status to the model, so it stated the 1990 rule (44 h) as "en vigueur".

## Limits
- 10 questions, hand-scored by one person, so the figures aren't a general measure. Two references are themselves doubtful: Q02 (13 is about part-time work) and Q07/Q08 (74 and 75 don't cover dismissal; 73-4 does). See `docs/baseline_results.md`.
- The RAG run is undated, so Q09 ("en 1997") isn't tested with a date.
- The citation verifier at run time only checked that cited article numbers were retrieved. The stricter verifier (quotes must appear in the article) was applied afterwards, offline; it led to Q08 being rescored.

## Next steps (P5 unless noted)
1. **Open: pass version status and dates to the model.** Add `version_status`, `valid_from` and `valid_to` from `search()` to each article in the context (`eval/rag_pipeline.py`, `build_prompt`). This fixes Q04-type answers.
2. **Done (2026-11-27): citation verifier** (`eval/citation_verifier.py`, 13 tests in `tests/test_citation_verifier.py`):
   - ✅ a correct refusal ("Je ne trouve pas de règle dans le corpus") with no citation is accepted (Q09, Q10);
   - ✅ an article only named inside a real quote isn't counted; one named in a retrieved article's text is reported as `named_in_context`, not invented (Q02, art. 12 named in 12 bis);
   - ✅ the non-breaking hyphen "‑" is read ("73‑4" becomes `73-4`, Q08);
   - ✅ every quoted passage must appear in the article it's attached to, ignoring formatting and punctuation, but not changed words.

   **Offline recheck of the 10 saved RAG answers** (no API call). The verifier result changes for 4 answers:
   - Q02, Q09, Q10 now **pass** (the old flags were false alarms).
   - **Q08 now fails**: its quote joins two paragraphs of art. 73-4. It ties "présumé abusif" to a breach of procedure, while the law ties it to a dismissal outside art. 73; a breach of procedure gives annulment plus compensation. The conclusion (the employee can contest; at least 6 months' salary when the dismissal is abusive) is still right, but the quote misstates the condition.

   `eval/rag_answers.csv` keeps the `citations_valid` values from the run. After this recheck, Maram rescored Q08 from yes to **partial (wrong_quote)**; the totals above include that change.
3. **Retrieval misses for P4 (Assia):** art. 12 for CDD questions (Q02, Q09), art. 73 for dismissal (Q07), art. 42 for leave (Q05). Also run Q09 with a date once dated search returns non-tracked articles such as 12.
4. **Test-set references for P4:** Q02 (drop 13), Q07/Q08 (use 73 and 73-1..73-6 instead of 74/75).

## Graph answers (added 2026-11-27)
Questions like "Quel texte a modifié l'article 73 ?" are now answered from Ikram's knowledge graph with no LLM call. Versions are checked with Mohcem's `get_version` / `list_versions`, and citations against the graph edges. See `docs/graph_answers.md`. That work also found a graph/P3 disagreement on article 73-4.

Note: Ikram's graph branch also updates `data/interim/articles.json` and `evolution_blocks.json` (splitter fix for articles 141–154). The LLM-alone, extraction and RAG results above came from the earlier text and haven't been rerun.
