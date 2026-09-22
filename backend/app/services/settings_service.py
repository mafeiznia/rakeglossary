"""Settings service — typed helpers on top of the key/value store."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.setting import Setting

log = get_logger("services.settings")

KEY_USER_STOPWORDS = "user_stopwords"


def get_raw(session: Session, key: str) -> str | None:
    row = session.get(Setting, key)
    return row.value if row else None


def set_raw(session: Session, key: str, value: str) -> Setting:
    row = session.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value)
        session.add(row)
    else:
        row.value = value
    session.commit()
    session.refresh(row)
    return row


def get_user_stopwords(session: Session) -> list[str]:
    """Return user-defined stopwords (lowercased, deduplicated, order preserved)."""
    raw = get_raw(session, KEY_USER_STOPWORDS)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("user_stopwords setting contains invalid JSON; returning [].")
        return []
    if not isinstance(data, list):
        return []

    seen: set[str] = set()
    result: list[str] = []
    for item in data:
        if not isinstance(item, str):
            continue
        w = item.strip().lower()
        if w and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def set_user_stopwords(session: Session, words: list[str]) -> list[str]:
    """Persist `words` after normalization (lowercase, strip, dedupe)."""
    seen: set[str] = set()
    normalized: list[str] = []
    for item in words:
        if not isinstance(item, str):
            continue
        w = item.strip().lower()
        if w and w not in seen:
            seen.add(w)
            normalized.append(w)

    set_raw(
        session,
        KEY_USER_STOPWORDS,
        json.dumps(normalized, ensure_ascii=False),
    )
    log.info(f"Updated user_stopwords ({len(normalized)} entries).")
    return normalized


def add_user_stopword(session: Session, word: str) -> list[str]:
    """Append a single word (idempotent). Returns the updated list."""
    current = get_user_stopwords(session)
    w = word.strip().lower()
    if w and w not in current:
        current.append(w)
        set_user_stopwords(session, current)
    return current


def remove_user_stopword(session: Session, word: str) -> list[str]:
    """Remove a word (no-op if absent). Returns the updated list."""
    current = get_user_stopwords(session)
    w = word.strip().lower()
    updated = [x for x in current if x != w]
    if updated != current:
        set_user_stopwords(session, updated)
    return updated
