"""
Simple disk cache for LLM responses.
Key = sha256(model + prompt)
Value = JSON file with {model, prompt, response, timestamp}
"""

import os
import json
import hashlib
from datetime import datetime, timezone

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(model: str, prompt: str) -> str:
    """Stable hash for a (model, prompt) pair."""
    raw = f"{model}::{prompt}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load(model: str, prompt: str):
    """Return cached response (str) or None if not cached."""
    path = os.path.join(CACHE_DIR, f"{_cache_key(model, prompt)}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["response"]


def save(model: str, prompt: str, response: str) -> str:
    """Save response to cache. Returns the file path."""
    path = os.path.join(CACHE_DIR, f"{_cache_key(model, prompt)}.json")
    payload = {
        "model": model,
        "prompt": prompt,
        "response": response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path
