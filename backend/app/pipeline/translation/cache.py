"""Persistent translation cache backed by diskcache."""

from __future__ import annotations

import hashlib

import diskcache

from app.core.config import settings

_CACHE = diskcache.Cache(str(settings.paths.cache / "translations"))


def _key(text: str, source: str, target: str) -> str:
    raw = f"{source}|{target}|{text}".encode()
    return hashlib.sha256(raw).hexdigest()


def get(text: str, source: str, target: str) -> str | None:
    return _CACHE.get(_key(text, source, target))


def set(text: str, source: str, target: str, translated: str) -> None:
    _CACHE.set(_key(text, source, target), translated)
