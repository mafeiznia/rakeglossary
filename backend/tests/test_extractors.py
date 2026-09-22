"""Tests for document extractors."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.pipeline.extractors import load_text, supported_extensions


def test_supported_extensions_contains_core_formats() -> None:
    exts = supported_extensions()
    for needed in (".pdf", ".docx", ".epub", ".txt"):
        assert needed in exts


def test_unsupported_extension_returns_empty(tmp_path: Path) -> None:
    f = tmp_path / "sample.xyz"
    f.write_text("irrelevant")
    assert load_text(f) == ""


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_text(tmp_path / "does_not_exist.txt") == ""


def test_txt_roundtrip(tmp_path: Path) -> None:
    f = tmp_path / "sample.txt"
    f.write_text("Hello world. This is a test.", encoding="utf-8")
    assert "Hello world" in load_text(f)


def test_txt_with_bom(tmp_path: Path) -> None:
    f = tmp_path / "bom.txt"
    f.write_bytes("\ufeffContent with BOM".encode("utf-8"))
    assert "Content with BOM" in load_text(f)