"""Pydantic schemas package."""

from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.glossary import (
    GlossaryEntryRead,
    GlossaryEntryUpdate,
    GlossaryResponse,
)
from app.schemas.project import (
    BookMetadataUpdate,
    ProcessRequest,
    ProjectCreateEmpty,
    ProjectListResponse,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)
from app.schemas.settings import (
    SettingRead,
    SettingUpdate,
    UserStopwordAdd,
    UserStopwordsRead,
)
from app.schemas.source import (
    ProjectSourceRead,
    ProjectSourceUpdate,
    TextSourceCreate,
)

__all__ = [
    "BookMetadataUpdate",
    "ErrorResponse",
    "GlossaryEntryRead",
    "GlossaryEntryUpdate",
    "GlossaryResponse",
    "PaginatedResponse",
    "ProcessRequest",
    "ProjectCreateEmpty",
    "ProjectListResponse",
    "ProjectRead",
    "ProjectSourceRead",
    "ProjectSourceUpdate",
    "ProjectSummary",
    "ProjectUpdate",
    "SettingRead",
    "SettingUpdate",
    "TextSourceCreate",
    "UserStopwordAdd",
    "UserStopwordsRead",
]
