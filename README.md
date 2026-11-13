# Qanun

Qanun is a student-built retrieval-augmented assistant for Algerian labor law, starting with Law 90-11. French is the primary data language. This repository contains the project scaffold; legal corpus ingestion and the end-to-end answer pipeline remain team tasks.

## Folder map

- `data/raw_pdf/`: original public gazette PDFs (ignored by Git except `.gitkeep`)
- `data/processed/`: extracted text and structured JSON
- `data/db/`: local SQLite database (ignored by Git)
- `src/collect/`, `src/structure/`: collection and article parsing
- `src/versions/`, `src/graph/`, `src/search/`, `src/rag/`, `src/ui/`, `src/common/`: legal versioning, graph, retrieval, answer pipeline, interface, and shared utilities
- `eval/`: retrieval and model evaluation templates
- `docs/`: data contract and team logs

## Setup

Use Python 3.11.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
python -m src.common.init_db
```

Set your own Groq API key and the teacher-approved model name in the ignored `config.yaml` (block `llm:`), or in environment variables / a local `.env` file: `QANUN_LLM_API_KEY` and `QANUN_LLM_MODEL`.

## Project rules

- The only generative model/API for this project is the one approved by the teacher: Groq, model `openai/gpt-oss-120b` (confirm the exact name; keep the teacher's written approval). No other LLM, no paid plan.
- Never commit API keys, `.env`, or `config.yaml`.
- Send only public legal texts and questions to the LLM API; do not send personal or confidential information.
- Respect `robots.txt` and applicable site terms when collecting documents. Do not scrape the Ministry of Commerce website.
- Legal durations and other legal values must come from retrieved legal articles, not constants in code.

## Module owners

| module | owner |
|---|---|
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |

## Run

```powershell
streamlit run src/ui/app.py
python -m eval.run_eval
python -m eval.baseline_llm_alone
```

Evaluation scripts contain TODOs until the retrieval and answer pipeline is connected. LLM responses are cached for replay without repeat calls (cache folder is git-ignored).

