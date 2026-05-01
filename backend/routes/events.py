"""SSE event stream route — placeholder for Phase 1."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/events/stream")
async def event_stream():
    # Will be implemented in commit 2 with SSE
    return {"status": "placeholder"}
