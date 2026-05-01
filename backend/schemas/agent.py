from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AgentRole(str, Enum):
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CRITIC = "critic"
    EXECUTOR = "executor"


class AgentStatus(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    NEGOTIATING = "negotiating"
    WORKING = "working"
    REVIEWING = "reviewing"
    PAID = "paid"
    SWAPPED = "swapped"


class Agent(BaseModel):
    id: str
    name: str
    role: AgentRole
    wallet_address: str
    status: AgentStatus
    memory_key: Optional[str] = None
