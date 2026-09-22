"""Load LLM provider metadata from a JSON file.

The JSON file lives next to this module (`llm_providers.json`) and can be
edited by users to add new OpenAI-compatible providers without touching
any Python code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.logging import get_logger

log = get_logger("llm.providers")

_JSON_PATH = Path(__file__).parent / "llm_providers.json"


@dataclass(frozen=True)
class ProviderInfo:
    key: str
    name: str
    base_url: str | None
    default_model: str
    suggested_models: tuple[str, ...]
    docs_url: str


def _load_from_json() -> dict[str, ProviderInfo]:
    try:
        raw = _JSON_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except FileNotFoundError:
        log.error(f"llm_providers.json not found at {_JSON_PATH}")
        return {}
    except json.JSONDecodeError as exc:
        log.error(f"llm_providers.json is invalid JSON: {exc}")
        return {}

    providers: dict[str, ProviderInfo] = {}
    for entry in data.get("providers", []):
        try:
            info = ProviderInfo(
                key=str(entry["key"]).lower(),
                name=str(entry["name"]),
                base_url=entry.get("base_url") or None,
                default_model=str(entry.get("default_model", "")),
                suggested_models=tuple(entry.get("suggested_models", [])),
                docs_url=str(entry.get("docs_url", "")),
            )
            providers[info.key] = info
        except (KeyError, TypeError) as exc:
            log.warning(f"Skipping malformed provider entry: {exc}")

    log.info(f"Loaded {len(providers)} LLM providers: {list(providers)}")
    return providers


@lru_cache(maxsize=1)
def _providers() -> dict[str, ProviderInfo]:
    return _load_from_json()


def get_provider(key: str) -> ProviderInfo | None:
    return _providers().get(key.lower())


def list_providers() -> list[ProviderInfo]:
    return list(_providers().values())


def reload_providers() -> None:
    """Clear the cache — call after editing the JSON file."""
    _providers.cache_clear()
