# LLM-assisted extraction on hard amendment cases (P5, week 3)

**Model:** `openai/gpt-oss-120b` via Groq (teacher-imposed model), through the disk cache `src/rag/llm_cache.py`. **11 API calls** in total: 9 on 2026-11-26, and 2 on 2026-11-27 after P3's new data (the 8 other prompts came from the cache). Only public legal text was sent. No Gemini result is used anywhere.

Reproduce with no new calls (everything replays from the cache):

```
QANUN_LLM_MODEL=openai/gpt-oss-120b python -m eval.llm_extraction   # -> data/interim/amendments_llm.csv
python -m eval.score_extraction                                      # -> eval/results/extraction_scores.json (no API call)
```

## Input (after P3 week 2, merged 2026-11-26)
P3 (Mohcem) rewrote `data/interim/amendments.csv` (79 records). All 79 rows of `P3_Modified_Articles.csv` are now `VERIFIED_OFFICIAL_JO`. The rule parser leaves **34 hard records**, which are sent as 10 prompts:

| Kind | Records | Amending text |
|---|---|---|
| `term_substitution`: "accord collectif" added in art. 115–133 | 17 | ord. 96-21 Art. 18 |
| Partial or rewritten: 12, 13, 31, 54, 97 | 5 | ord. 96-21 Art. 2, 4, 5, 8, 13 |
| Rewritten by the 2018 finance law: 142, 143, 143 bis, 146, 146 bis, 147, 148, 150, 151, 152, 154 | 11 | loi 17-11 Art. 99 (3 prompts) |
| New article 73-4 | 1 | loi 91-29 Art. 3 |

The 87 bis repeal is no longer a hard case: P3 verified it as **loi 14-10 (finance law for 2015), Art. 90**, and the rules now say the same.

For each prompt, the model receives the public passage from `data/interim/evolution_blocks.json`: about 500 characters before the instruction, plus the instruction and the quoted text. It must return JSON records, each with an exact `evidence` quote. Every output row has `extraction_method = llm`, `status = à vérifier` and `model = openai/gpt-oss-120b`.

## Scores against the verified P3 rows
Gold standard: the verified P3 row for each hard record, matched on (article, amending text). All 34 have one. The comparison unit is (article, action, amending text number).

| Method | Records | Correct | Precision | Recall |
|---|---|---|---|---|
| Rules (P2 parser) | 34 | 34 | 1.000 | 1.000 |
| LLM, strict | 35 | 22 | 0.629 | 0.647 |
| LLM, ignoring the action label | 33 | 23 | 0.697 | 0.676 |

Why the LLM misses 12 of 34:
- **11 records with no amending text** (loi 17-11 group and 143 bis). The passage sent starts at "Art. 99. — Les dispositions des articles 141, 142, …" and never names loi 17-11. The model correctly marks them `uncertain` and leaves the text empty instead of guessing. This is a limit of the input passage, not an invention: the rules know the text from the document structure.
- **73-4 missed.** That passage doesn't name loi 91-29 either. The model returns one record, "art. 73 completed by Art. 3" (uncertain), instead of the inserted article 73-4.
- **Action label disagreements (2):**
  - 97: `modify` vs `complete`. The text says "complété et rédigé comme suit", so both readings are defensible.
  - 146 bis: `insert` vs `modify`. The LLM attaches loi 17-11 to the original insertion, which was ord. 96-21 Art. 21 (verified). This is the one confident wrong attribution.

## Invention check (all 42 LLM records)
- **0 invented:** no target article or text number absent from the passage sent.
- **13 edited quotes:** the evidence isn't word-for-word, because the model shortened the article list ("les articles 142 ... de la loi"). The article cited is real; only the quote is cut.
- **Extra records** outside the hard records, kept apart and not scored: 12 bis inserted by ord. 96-21 Art. 3 (matches a verified row), "73 completed by Art. 3", and 141, 143 bis, 144, 145, 146 bis rewritten by Art. 99 (text not identified).

## Conclusion
On these hard cases the LLM doesn't beat the rules: the rules get all 34 verified records right. The LLM's useful behaviour is honest uncertainty. It never invented a text number, and it said "uncertain" when the passage didn't name the amending text. Its errors are 1 wrong attribution (146 bis insert) and missing structure the rules get from the document layout. Possible improvement: send the header of the amending text with each passage, which would need new calls. Every LLM row stays `à vérifier`, and none replaces a rule record.

## Limits
- The gold set is 34 records from 4 amending texts (ord. 96-21, loi 17-11, loi 91-29), so precision and recall here aren't a general measure.
- The rule records and P3's list may share a source (the annotated consolidated text), so their full agreement isn't independent proof.
- The invention check is mechanical: it catches articles and numbers absent from the passage, but not real ones attached to the wrong event (146 bis).
