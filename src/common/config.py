"""Load project configuration from config.yaml and environment overrides."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

try:  # optional: lets a local .env file provide the variables
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load config.yaml; QANUN_* environment variables override its values."""
    config_path = Path(path) if path else ROOT / "config.yaml"
    config: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    llm = config.setdefault("llm", {})
    paths = config.setdefault("paths", {})
    # GROQ_API_KEY is accepted as a fallback so existing .env files keep working.
    api_key = os.getenv("QANUN_LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    if api_key:
        llm["api_key"] = api_key
    if os.getenv("QANUN_LLM_MODEL"):
        llm["model"] = os.environ["QANUN_LLM_MODEL"]
    for key, env in (("db", "QANUN_DB_PATH"), ("cache", "QANUN_CACHE_PATH")):
        if os.getenv(env):
            paths[key] = os.environ[env]
    if not llm.get("api_key") or llm["api_key"] == "PUT_YOUR_KEY_HERE":
        raise ValueError("LLM API key missing. Set QANUN_LLM_API_KEY or add it to the ignored config.yaml.")
    if not llm.get("model") or llm["model"].startswith("["):
        raise ValueError("LLM model missing. Set QANUN_LLM_MODEL or fill it in config.yaml.")
    return config


def resolve_path(value: str) -> Path:
    """Resolve a configured path relative to the project root."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path
