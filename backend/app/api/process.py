"""Process endpoints: start pipeline, stream progress via SSE."""

from __future__ import annotations

import asyncio
import json
import queue

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api._helpers import project_to_read
from app.api.deps import ProjectDep, SessionDep
from app.core.logging import get_logger
from app.models.project import ProjectStatus
from app.schemas.project import ProcessRequest, ProjectRead
from app.services import pipeline_runner, project_service
from app.services.progress import ProgressEvent, tracker

log = get_logger("api.process")

router = APIRouter(prefix="/api", tags=["process"])


@router.post(
    "/process/{project_id}",
    response_model=ProjectRead,
    summary="Start the glossary pipeline for a project",
)
def start_process(
    project: ProjectDep,
    payload: ProcessRequest,
    session: SessionDep,
) -> ProjectRead:
    if project.status == ProjectStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project is already being processed.",
        )

    project_service.apply_process_options(session, project, payload)
    project_service.mark_processing(session, project)

    pipeline_runner.start_pipeline(project.id)

    session.refresh(project)
    return project_to_read(project)


async def _event_stream(project_id: str):
    """Yield SSE-formatted events for the given project."""
    history = tracker.history(project_id)
    for ev in history:
        yield _format_sse(ev)

    q = tracker.subscribe(project_id)
    try:
        while True:
            try:
                item = await asyncio.to_thread(q.get, True, 15.0)
            except queue.Empty:
                yield ": keep-alive\n\n"
                continue

            if tracker.is_sentinel(item):
                break

            if isinstance(item, ProgressEvent):
                yield _format_sse(item)
    finally:
        tracker.unsubscribe(project_id, q)


def _format_sse(event: ProgressEvent) -> str:
    payload = json.dumps(event.to_dict(), ensure_ascii=False)
    return f"event: progress\ndata: {payload}\n\n"


@router.get(
    "/process/{project_id}/events",
    summary="Server-Sent Events stream of pipeline progress",
)
async def stream_progress(project_id: str) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(project_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/process/{project_id}/cancel",
    response_model=ProjectRead,
    summary="Cancel a running pipeline (cooperative)",
)
def cancel_process(project: ProjectDep, session: SessionDep) -> ProjectRead:
    if project.status != ProjectStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project is not currently processing.",
        )
    cancelled = pipeline_runner.cancel_pipeline(project.id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No live pipeline found for this project.",
        )
    session.refresh(project)
    return project_to_read(project)
