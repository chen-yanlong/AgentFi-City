"""Demo orchestration routes — placeholder for Phase 1."""

from fastapi import APIRouter

router = APIRouter(prefix="/demo")


@router.post("/start")
async def start_demo():
    # Will be implemented in commit 2
    return {"demo_id": "not-implemented", "status": "placeholder"}


@router.post("/reset")
async def reset_demo():
    # Will be implemented in commit 2
    return {"status": "reset"}


@router.get("/state")
async def get_state():
    # Will be implemented in commit 2
    return {"status": "placeholder"}
