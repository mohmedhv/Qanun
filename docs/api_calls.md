# External API call log

The LLM wrapper (`src/rag/llm_cache.py`, Groq) records every uncached provider call as one JSON line in the ignored cache directory's `api_calls.jsonl`. Never put keys or private data in the log.

| date | member | purpose | number of calls |
|---|---|---|---|
| 2026-11-13 | Maram | LLM-alone baseline on 10 questions | non disponible : cache/API log absent du workspace; 10 questions ne prouvent pas 10 appels |

