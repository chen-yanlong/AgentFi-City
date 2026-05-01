"""Demo orchestration routes."""

import asyncio

from fastapi import APIRouter, HTTPException

from backend.state import demo_state
from backend.orchestrator import run_demo

router = APIRouter(prefix="/demo")


@router.post("/start")
async def start_demo():
    if demo_state.is_running:
        raise HTTPException(status_code=409, detail="Demo is already running")

    demo_state.reset()
    asyncio.create_task(run_demo())

    return {"demo_id": demo_state.demo_id or "starting", "status": "started"}


@router.post("/reset")
async def reset_demo():
    demo_state.reset()
    return {"status": "reset"}


@router.get("/state")
async def get_state():
    return {
        "demo_id": demo_state.demo_id,
        "is_running": demo_state.is_running,
        "agents": [a.model_dump() for a in demo_state.agents],
        "task": demo_state.task.model_dump() if demo_state.task else None,
        "events": [e.model_dump() for e in demo_state.events],
    }
