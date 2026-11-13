"""
LLM client that ALWAYS checks cache first.
Only calls Groq if the prompt is not in cache.
Logs the number of real API calls.
"""

import os
import requests
from dotenv import load_dotenv

from llm_cache import load, save

load_dotenv()

MODEL = "openai/gpt-oss-120b"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

# Counter for real API calls made (excluding cache hits)
API_CALL_COUNT = 0


def ask(prompt: str, system_prompt: str = None) -> str:
    """
    Ask the LLM. Uses cache if available; otherwise calls Groq.
    Returns the raw text response.
    """
    global API_CALL_COUNT

    # Build a stable "full prompt" key for caching
    full_prompt = (system_prompt or "") + "\n---USER---\n" + prompt

    # 1. Try cache first
    cached = load(MODEL, full_prompt)
    if cached is not None:
        return cached

    # 2. Not in cache → call the API
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages},
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Groq API error {response.status_code}: {response.text[:300]}"
        )

    API_CALL_COUNT += 1
    answer = response.json()["choices"][0]["message"]["content"]

    # 3. Save to cache
    save(MODEL, full_prompt, answer)
    return answer


def get_api_call_count() -> int:
    """How many real API calls were made in this session (excludes cache hits)."""
    return API_CALL_COUNT
