"""Runtime helper for real AXL mode.

Holds one AXLClient per agent (each pointing at that agent's local AXL node)
and discovers their peer IDs via /topology on startup. Returns None when
USE_REAL_AXL is off or any node is unreachable — orchestrator falls back to
emit-only AXL events.

Design note: the Python backend stays single-process for simplicity; the
"separate processes" requirement of the bounty is satisfied by the four AXL
node binaries (each its own OS process).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from backend.config import get_settings
from backend.services.axl_service import AXLClient, AXLMessage, AXLUnavailable

logger = logging.getLogger(__name__)


@dataclass
class AXLRuntime:
    clients: dict[str, AXLClient]  # agent_id -> client
    peer_ids: dict[str, str]  # agent_id -> hex peer_id

    async def send_and_recv(
        self,
        from_agent: str,
        to_agent: str,
        msg_type: str,
        body: dict,
        recv_timeout: float = 5.0,
    ) -> tuple[AXLMessage, AXLMessage]:
        """Send from_agent → to_agent over AXL; poll receiver for the matching
        msg_id. Returns (sent, received). Raises AXLUnavailable on timeout."""
        sender = self.clients[from_agent]
        receiver = self.clients[to_agent]
        to_peer_id = self.peer_ids[to_agent]

        sent = await sender.send(to_peer_id, to_agent, msg_type, body)

        loop = asyncio.get_event_loop()
        deadline = loop.time() + recv_timeout
        while loop.time() < deadline:
            received = await receiver.recv(timeout_sec=1.0)
            if received and received.msg_id == sent.msg_id:
                return sent, received
            await asyncio.sleep(0.1)
        raise AXLUnavailable(
            f"recv timeout: {from_agent}→{to_agent} msg_id={sent.msg_id}"
        )

    async def broadcast(
        self,
        from_agent: str,
        to_agents: list[str],
        msg_type: str,
        body: dict,
    ) -> list[tuple[AXLMessage, AXLMessage]]:
        """Fan-out send + recv. Returns list of (sent, received) per recipient."""
        results = []
        for to_agent in to_agents:
            results.append(
                await self.send_and_recv(from_agent, to_agent, msg_type, body)
            )
        return results


_AGENT_TO_URL_KEY = {
    "planner-001": "axl_planner_url",
    "researcher-001": "axl_researcher_url",
    "critic-001": "axl_critic_url",
    "executor-001": "axl_executor_url",
}


async def get_axl_runtime() -> Optional[AXLRuntime]:
    """Returns AXLRuntime if real-mode is enabled and all 4 nodes are
    reachable; otherwise None so orchestrator falls back."""
    settings = get_settings()
    if not settings.use_real_axl:
        return None

    clients: dict[str, AXLClient] = {}
    peer_ids: dict[str, str] = {}

    for agent_id, url_key in _AGENT_TO_URL_KEY.items():
        url = getattr(settings, url_key)
        client = AXLClient(url, agent_id=agent_id)
        try:
            topo = await client.topology()
        except AXLUnavailable as e:
            logger.warning(
                "AXL real-mode disabled: %s unreachable at %s (%s)", agent_id, url, e
            )
            return None
        if not topo.self_peer_id:
            logger.warning(
                "AXL real-mode disabled: %s topology missing peer_id", agent_id
            )
            return None
        clients[agent_id] = client
        peer_ids[agent_id] = topo.self_peer_id

    logger.info("AXL real-mode ready with %d nodes", len(clients))
    return AXLRuntime(clients=clients, peer_ids=peer_ids)
