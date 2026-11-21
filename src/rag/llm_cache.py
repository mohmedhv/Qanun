"""Disk cache around the project LLM (Groq, teacher-approved).

Same model + same prompt -> the answer is read from disk, no new API call.
Every real (uncached) call is appended to <cache dir>/api_calls.jsonl so the
report can state the number of calls.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone

import requests

from src.common.config import load_config, resolve_path

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _key(model: str, full_prompt: str) -> str:
    """Stable hash for a (model, prompt) pair."""
    return hashlib.sha256(f"{model}::{full_prompt}".encode("utf-8")).hexdigest()


def generate_cached(prompt: str, model_name: str | None = None,
                    system_instruction: str | None = None,
                    config: dict | None = None) -> str:
    """Return the cached answer, or call the LLM once and save it."""
    settings = config or load_config()
    llm = settings["llm"]
    model_name = model_name or llm["model"]
    cache_dir = resolve_path(settings.get("paths", {}).get("cache", "cache/llm"))
    cache_dir.mkdir(parents=True, exist_ok=True)

    full_prompt = (system_instruction or "") + "\n---USER---\n" + prompt
    cache_file = cache_dir / f"{_key(model_name, full_prompt)}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))["response"]

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    response = None
    for _ in range(5):  # retry when the free tier answers 429 (rate limit)
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {llm['api_key']}"},
            json={"model": model_name, "messages": messages},
            timeout=60,
        )
        if response.status_code != 429:
            break
        time.sleep(20)
    if response is None or response.status_code != 200:
        raise RuntimeError(f"LLM API error {response.status_code}: {response.text[:300]}")

    answer = response.json()["choices"][0]["message"]["content"]
    now = datetime.now(timezone.utc).isoformat()
    cache_file.write_text(
        json.dumps({"model": model_name, "prompt": full_prompt, "response": answer,
                    "timestamp": now}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (cache_dir / "api_calls.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"date": now, "model": model_name,
                              "purpose": "uncached LLM generation", "count": 1}) + "\n")
    time.sleep(llm.get("delay_seconds", 5))  # stay under the free-tier tokens/minute limit
    return answer
