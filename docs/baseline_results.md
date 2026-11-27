# LLM-alone baseline: results (P5)

**Model:** `openai/gpt-oss-120b` via Groq (teacher-imposed model). **10 API calls**, made on 2026-11-26, with no retrieval and no system prompt. These are the "before" figures for the LLM-alone vs RAG comparison. No Gemini result is used.

- **Prompt:** Q01–Q09 are sent as "En droit algérien, …". Q10 (out of scope) is sent as written: "Quel est le préavis de démission en France ?".
- **Data:** `eval/baseline_llm_alone.csv` (answers, model, hand scores, cited articles, notes).
- **Reproduce:** `QANUN_LLM_MODEL=openai/gpt-oss-120b python -m eval.baseline_llm_alone` replays from the cache with no new call. Rerunning overwrites the hand-score columns, so keep a copy first.
- **Scoring:** done by hand by Maram against the 1997 text of loi 90-11 in `data/interim/articles.json`.

## Summary

| Result | Questions | Count |
|---|---|---|
| Correct | — | **0 / 10** |
| Partly correct | Q01, Q02, Q04, Q05 | 4 / 10 |
| Wrong | Q03, Q06, Q07, Q08, Q09, Q10 | 6 / 10 |
| Out-of-scope question refused | — | 0 / 1 (Q10 answered from French law) |

| Error type (several per answer possible) | Questions | Count |
|---|---|---|
| invented_article (non-existent text, wrong article number or invented content) | Q01–Q09 | 9 |
| wrong_figure | Q03, Q06 | 2 |
| foreign_law (French-law concepts) | Q07, Q08 | 2 |
| wrong_version | Q09 | 1 |
| no_version | Q04 | 1 |
| out_of_scope_answered | Q10 | 1 |

## What we learn
- **Adding "En droit algérien" changes the kind of error, not the score.** The first run (13/11) answered every question from French law. Now the model talks about Algeria, but it invents Algerian-looking sources:
  - "Ordonnance 90-08 portant Code du travail" (Q04)
  - "Décret 85-11" (Q02)
  - "Ordonnance 66-03" as the 1997 code (Q09)
  - a wrong date for loi 90-11 (Q09)
  - court rulings and books that can't be checked (Q01, Q03, Q09)
- **No answer cites the right article.** Even partly right answers (Q01 oral contract, Q05 2.5 days per month) rest on wrong article numbers.
- **Some figures are wrong in a dangerous way.** Q06 says overtime is paid +25 %, while art. 32 sets a minimum of +50 %. Q03 says a 3-month trial period, while art. 18 allows up to 6 (12 for highly qualified posts).
- **No version awareness.** Q04 gives 40 h/week, probably the rule after ord. 97-03, without saying the 1990 text (art. 22) said 44 h. Q09 misses ord. 96-21, which changed the CDD rules in 1996.
- **No refusal.** Q10 gets a full French-law answer with a model letter. Refusing must come from the RAG system prompt and the "no rule in the corpus" check.

## Problems found in the test set (to fix with P4)
- **Q02:** reference 13 is about part-time work, not CDD. Art. 12 (plus 12 bis since 1996) is the right reference.
- **Q07 / Q08:** references 74 (change of employer) and 75 (internal rules) don't answer the questions. The dismissal procedure and its appeal are in 73-1 to 73-6 (added by loi 91-29), which aren't in the 158-article corpus.
- **Q04 / Q09:** dated answers depend on the amendments (ord. 97-03 for art. 22, ord. 96-21 for art. 12). They can only be scored properly once P3's version records exist.
- **Corpus typo:** art. 18 reads "dix (06) mois".
