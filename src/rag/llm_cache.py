"""Disk cache around Gemini; uncached calls are counted in an ignored JSONL log."""
from datetime import datetime, timezone
import hashlib
import json
from src.common.config import load_config, resolve_path
import google.generativeai as genai


def generate_cached(prompt: str, model_name: str | None = None, system_instruction: str | None = None,
                    config: dict | None = None) -> str:
    """Read a model+prompt cache entry or call Gemini once and save it."""
    settings = config or load_config()
    model_name = model_name or settings["gemini"]["model"]
    cache_dir = resolve_path(settings.get("paths", {}).get("cache", "cache/llm"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{model_name}\0{system_instruction or ''}\0{prompt}".encode()).hexdigest()
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))["response"]
    genai.configure(api_key=settings["gemini"]["api_key"])
    model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
    answer = model.generate_content(prompt).text
    cache_file.write_text(json.dumps({"model": model_name, "response": answer}, ensure_ascii=False, indent=2), encoding="utf-8")
    with (cache_dir / "api_calls.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"date": datetime.now(timezone.utc).isoformat(), "model": model_name,
                              "purpose": "uncached Gemini generation", "count": 1}) + "\n")
    return answer

