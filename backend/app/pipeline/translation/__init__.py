"""Translation package."""

from app.pipeline.translation.service import (
    get_translator,
    translate,
    translate_many,
)

__all__ = ["get_translator", "translate", "translate_many"]
