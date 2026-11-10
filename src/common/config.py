"""Load project configuration from config.yaml and environment overrides."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load config.yaml; QANUN_* environment variables override its values."""
    config_path = Path(path) if path else ROOT / "config.yaml"
    config: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    gemini = config.setdefault("gemini", {})
    paths = config.setdefault("paths", {})
    for key, env in (("api_key", "QANUN_GEMINI_API_KEY"), ("model", "QANUN_GEMINI_MODEL")):
        if os.getenv(env):
            gemini[key] = os.environ[env]
    for key, env in (("db", "QANUN_DB_PATH"), ("cache", "QANUN_CACHE_PATH")):
        if os.getenv(env):
            paths[key] = os.environ[env]
    if not gemini.get("api_key") or gemini["api_key"] == "PUT_YOUR_KEY_HERE":
        raise ValueError("Gemini API key missing. Set QANUN_GEMINI_API_KEY or add it to ignored config.yaml.")
    if not gemini.get("model") or gemini["model"].startswith("["):
        raise ValueError("Gemini model missing. Set QANUN_GEMINI_MODEL or choose the teacher-announced model in config.yaml.")
    return config


def resolve_path(value: str) -> Path:
    """Resolve a configured path relative to the project root."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path

