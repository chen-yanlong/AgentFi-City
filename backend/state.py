"""In-memory demo state management."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.schemas.agent import Agent, AgentRole, AgentStatus
from backend.schemas.task import Task, TaskStatus
from backend.schemas.events import DemoEvent, EventType


class DemoState:
    """Holds all runtime state for a single demo run."""

    def __init__(self) -> None:
        self.demo_id: Optional[str] = None
        self.agents: list[Agent] = []
        self.task: Optional[Task] = None
        self.events: list[DemoEvent] = []
        self.is_running: bool = False
        self._subscribers: list[asyncio.Queue[DemoEvent]] = []
        self._init_agents()

    def _init_agents(self) -> None:
        self.agents = [
            Agent(
                id="planner-001",
                name="Planner",
                role=AgentRole.PLANNER,
                wallet_address="0x0000000000000000000000000000000000000001",
                status=AgentStatus.IDLE,
            ),
            Agent(
                id="researcher-001",
                name="Researcher",
                role=AgentRole.RESEARCHER,
                wallet_address="0x0000000000000000000000000000000000000002",
                status=AgentStatus.IDLE,
            ),
            Agent(
                id="executor-001",
                name="Executor",
                role=AgentRole.EXECUTOR,
                wallet_address="0x0000000000000000000000000000000000000003",
                status=AgentStatus.IDLE,
            ),
        ]

    def reset(self) -> None:
        self.demo_id = None
        self.task = None
        self.events = []
        self.is_running = False
        self._init_agents()

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None

    def set_agent_status(self, agent_id: str, status: AgentStatus) -> None:
        agent = self.get_agent(agent_id)
        if agent:
            agent.status = status

    def subscribe(self) -> asyncio.Queue[DemoEvent]:
        queue: asyncio.Queue[DemoEvent] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[DemoEvent]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def emit_event(
        self,
        event_type: EventType,
        source: str,
        message: str,
        metadata: dict | None = None,
    ) -> DemoEvent:
        event = DemoEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            type=event_type,
            message=message,
            metadata=metadata or {},
        )
        self.events.append(event)
        for queue in self._subscribers:
            queue.put_nowait(event)
        return event


# Singleton instance
demo_state = DemoState()
