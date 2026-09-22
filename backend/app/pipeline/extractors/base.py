"""Abstract base class for document extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentExtractor(ABC):
    """Base class for all document extractors.

    Each subclass must implement `supported_extensions` and `extract`.
    """

    supported_extensions: tuple[str, ...] = ()

    @abstractmethod
    def extract(self, file_path: Path) -> str:
        """Return plain text extracted from `file_path`.

        Implementations should never raise for missing/invalid files;
        instead log the error and return an empty string.
        """
        raise NotImplementedError
