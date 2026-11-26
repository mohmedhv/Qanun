# AI usage log

Project LLM: Groq, model `openai/gpt-oss-120b`. The teacher's written return dated 2026-11-21 reiterates that this model was confirmed in week 1 for every team. Keep that return with the course records. No Gemini result is used or reported; any Gemini output would not be comparable and is not part of the project.

| member | tool | purpose | date |
|---|---|---|---|
| Maram | Groq (`openai/gpt-oss-120b`) | LLM-alone baseline on the first 10 questions (first run, not recorded locally) | 2026-11-13 |
| Maram | Groq (`openai/gpt-oss-120b`) | RAG pipeline test on 1 question (1 call) | 2026-11-21 |
| Maram | Groq (`openai/gpt-oss-120b`) | LLM-alone baseline rerun with "En droit algérien" (10 calls); answers scored by hand | 2026-11-26 |
| Maram | Groq (`openai/gpt-oss-120b`) | Extraction of hard amendment cases (9 calls); output labelled `extraction_method = llm`, `à vérifier`. See `docs/llm_extraction.md` | 2026-11-26 |
| Maram | Claude Code (coding assistant) | Help writing and checking the P5 scripts (rag_pipeline fixes, baseline, extraction, scoring) and these docs; every result was reviewed by Maram | 2026-11-26 |
