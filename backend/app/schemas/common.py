"""Shared Pydantic schemas: pagination, error responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Standard error payload returned by the API."""

    detail: str = Field(..., description="Human-readable error message")
    code: str | None = Field(default=None, description="Optional machine-readable code")


class PaginatedResponse[T](BaseModel):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 50
