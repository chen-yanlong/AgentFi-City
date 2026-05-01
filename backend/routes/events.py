"""SSE event stream route."""

import asyncio
import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from backend.state import demo_state

router = APIRouter()


@router.get("/events/stream")
async def event_stream(request: Request):
    queue = demo_state.subscribe()

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event.type.value,
                        "data": json.dumps(event.model_dump()),
                    }
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield {"comment": "keepalive"}
        finally:
            demo_state.unsubscribe(queue)

    return EventSourceResponse(generate())
