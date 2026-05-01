from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TaskStatus(str, Enum):
    CREATED = "created"
    BROADCASTED = "broadcasted"
    TEAM_FORMING = "team_forming"
    TEAM_FORMED = "team_formed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    SETTLED = "settled"
    SWAPPED = "swapped"
    MEMORY_SAVED = "memory_saved"


class Task(BaseModel):
    id: str
    onchain_task_id: Optional[int] = None
    title: str
    description: str
    reward_token: str = "ETH"
    reward_amount: str = "0.01"
    status: TaskStatus = TaskStatus.CREATED
    participants: list[str] = []
    tx_hashes: list[str] = []
