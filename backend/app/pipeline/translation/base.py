"""Abstract translation provider."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Translator(ABC):
    """Common interface for all translation providers."""

    name: str = "base"

    @abstractmethod
    def translate(self, text: str, source: str = "en", target: str = "fa") -> str:
        """Translate `text` and return the translated string.

        Must not raise on empty input; may raise on network errors.
        """
        raise NotImplementedError

    def translate_batch(
        self, texts: list[str], source: str = "en", target: str = "fa"
    ) -> list[str]:
        """Translate a list of texts.

        Default implementation loops over `translate`. Providers that
        support a true batch API should override this.
        """
        return [self.translate(t, source=source, target=target) for t in texts]
