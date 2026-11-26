# LLM-assisted extraction on hard amendment cases (P5, week 3)

**Model:** `openai/gpt-oss-120b` via Groq (teacher-imposed model), through the disk cache `src/rag/llm_cache.py`. **9 API calls**, made on 2026-11-26. Only public legal text was sent. No Gemini result is used anywhere in this work.

Reproduce with no new calls (everything replays from the cache):

```
QANUN_LLM_MODEL=openai/gpt-oss-120b python -m eval.llm_extraction   # -> data/interim/amendments_llm.csv
python -m eval.score_extraction                                      # -> eval/results/extraction_scores.json (no API call)
```

## What was sent to the model
The P2 rule parser (`data/interim/amendments.csv`, 59 records) leaves 25 records it can't handle with certainty:

| Kind | Records | Calls |
|---|---|---|
| `term_substitution`: Art. 18 of ord. 96-21 adds "accord collectif" in 17 articles (115–133) | 17 | 1 (one sentence) |
| `partial` (only part of the new text is quoted): 12, 13, 31, 54, 97, 143 bis, 146 bis | 7 | 7 |
| Uncertain repeal of 87 bis (the nearest header is an application decree, 15-107) | 1 | 1 |

For each group, the model receives the public passage from `data/interim/evolution_blocks.json`: about 500 characters before the instruction, plus the instruction and the quoted text. It must return JSON records, each with an exact `evidence` quote from the passage. Every output row has `extraction_method = llm`, `status = à vérifier` and `model = openai/gpt-oss-120b`.

## Scores against Mohcem's verified P3 rows
Gold standard: the rows of `P3_Modified_Articles.csv` with status `VERIFIED_*`. Six groups have verified rows (ord. 96-21, Art. 2, 4, 5, 8, 13, 18), which gives **22 gold records**. The comparison unit is (article, action, amending text number).

| Method | Records | Correct | Precision | Recall |
|---|---|---|---|---|
| Rules (P2 parser) | 22 | 22 | 1.000 | 1.000 |
| LLM, strict | 22 | 21 | 0.955 | 0.955 |
| LLM, ignoring the action label | 22 | 22 | 1.000 | 1.000 |

- **The only strict LLM miss:** article 97. The LLM says `modify`, while P3 and the rules say `complete`. The text says "est complété et rédigé comme suit", so both readings are defensible; it's a labelling disagreement, not an invented fact.
- **Invention check:**
  - 0 of 28 LLM records have an evidence quote, target article or text number that is absent from the passage sent.
  - That check does **not** catch a real text named for the wrong event (see 146 bis below).
- **Extra record** outside the hard case: the LLM also extracted 12 bis inserted by ord. 96-21 Art. 3, because it was in the same passage. That record matches a verified P3 row.

On these hard cases, the LLM doesn't beat the rules: the rules already get all 22 verified records right. The LLM's value is in the cases below, where it says it's uncertain instead of guessing.

## Cases that cannot be scored (no verified P3 row): à vérifier

| Article | Rules | LLM | P3 (unverified) | Note |
|---|---|---|---|---|
| 87 bis repeal | décret exécutif 15-107, Art. 90 | repeal, Art. 90, text **not identified**, `uncertain = true` | loi 14-10 (LF 2015), Art. 90 | The LLM doesn't invent a number. It still names the text type as a "Décret exécutif". Check in the official JO. |
| 143 bis | modify by loi 17-11, Art. 99 | (1) insert by "Art. 20", text not identified, uncertain; (2) modify, article and text not specified, uncertain | modify by loi 17-11, Art. 99 | The LLM is cautious, but it loses the 17-11 attribution. |
| 146 bis | modify by loi 17-11, Art. 99 | (1) **insert by loi 17-11 Art. 99: wrong**; (2) modify by loi 17-11 Art. 99 | modify by loi 17-11, Art. 99 | 146 bis was inserted by Art. 21 of ord. 96-21 (a verified P3 row). The LLM attached the later text to the earlier insertion. |

**LLM error found:** 1 confident wrong attribution (the 146 bis insert), out of 6 records in these unverifiable groups. None of the LLM records replaces the rule records. They stay `à vérifier` until P3 checks them in the official JO.

## Limits
- The gold set is small (22 records, 6 instructions, all from ordonnance 96-21), so precision and recall here aren't a general measure.
- The rule records and P3's list may share a source (the annotated consolidated text), so agreement between them isn't independent proof.
- The invention check is mechanical: it catches quotes, articles and numbers that are absent from the passage, but not real ones attached to the wrong event.
