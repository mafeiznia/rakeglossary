"""Shared pytest configuration for all tests.

Ensures that all ORM models are registered with `Base.metadata` before
any test creates tables. Without this, `Base.metadata.create_all()`
would silently create an empty schema.
"""
from __future__ import annotations

# Importing this package registers Project, GlossaryEntry, and Setting
# with `Base.metadata`. Must run before any `create_all()` call.
from app import models  # noqa: F401