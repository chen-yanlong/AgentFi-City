from enum import Enum
from typing import Any

from pydantic import BaseModel


class EventType(str, Enum):
    TASK_CREATED = "task_created"
    AXL_MESSAGE = "axl_message"
    AGENT_DECISION = "agent_decision"
    CRITIC_REVIEW = "critic_review"
    CONTRACT_TX = "contract_tx"
    UNISWAP_QUOTE = "uniswap_quote"
    UNISWAP_SWAP = "uniswap_swap"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    ERROR = "error"
    DONE = "done"


class DemoEvent(BaseModel):
    id: str
    timestamp: str
    source: str
    type: EventType
    message: str
    metadata: dict[str, Any] = {}
