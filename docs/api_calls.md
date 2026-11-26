# External API call log

The LLM wrapper (`src/rag/llm_cache.py`, Groq) records every uncached provider call as one JSON line in the ignored cache directory's `api_calls.jsonl`. Never put keys or private data in the log. Counts below come from that file (line count before and after each run). All calls use `openai/gpt-oss-120b`; the fallback `openai/gpt-oss-20b` was never used.

| date | member | model | purpose | number of calls |
|---|---|---|---|---|
| 2026-11-13 | Maram | openai/gpt-oss-120b | First LLM-alone baseline, 10 questions, no jurisdiction in the prompt | not recorded: this cache and log are absent from the workspace. The results were replaced by the 2026-11-26 rerun. |
| 2026-11-21 | Maram | openai/gpt-oss-120b | RAG pipeline test, 1 question ("Un contrat de travail peut-il être oral ?") | 1 |
| 2026-11-26 | Maram | openai/gpt-oss-120b | LLM-alone baseline rerun, 10 questions, prompt "En droit algérien, …" (Q10, out of scope, sent as written) | 10 |
| 2026-11-26 | Maram | openai/gpt-oss-120b | LLM-assisted extraction on 25 hard amendment records (9 prompts) | 9 |
| 2026-11-26 | Maram | openai/gpt-oss-120b | Replay of the extraction from the cache | 0 |
| **Total logged** | | | | **20** |
