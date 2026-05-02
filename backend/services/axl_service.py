"""Python client for a local AXL node.

AXL exposes an HTTP admin API on the port configured per node (we use 7001-7004
for planner / researcher / critic / executor). This module wraps the three
endpoints we need:

  GET  /topology                                — query peer info
  POST /send  (header X-Destination-Peer-Id)    — send raw bytes to a peer
  GET  /recv  (returns body + X-From-Peer-Id)   — poll for the next inbound msg

All inter-agent messages are JSON-encoded (the wire is bytes, AXL doesn't care).
A2A-style structured envelope: { msg_id, from, to, type, body, timestamp }.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class AXLUnavailable(Exception):
    """Raised when the AXL node isn't reachable or returns a non-success status."""


@dataclass
class AXLMessage:
    msg_id: str
    from_peer: str  # AXL peer ID
    from_agent: str  # logical agent name (e.g. "planner-001")
    to_agent: str  # logical agent name; "broadcast" for fan-out
    type: str  # e.g. "TASK_ANNOUNCEMENT", "JOIN_PROPOSAL"
    body: dict
    timestamp: str


@dataclass
class AXLTopology:
    self_peer_id: str
    connected_peers: list[str]
    raw: dict


class AXLClient:
    """Talks to a single local AXL node's admin HTTP API."""

    def __init__(self, base_url: str, agent_id: str):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id

    async def topology(self) -> AXLTopology:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/topology")
        except httpx.HTTPError as e:
            raise AXLUnavailable(f"node unreachable: {e}") from e
        if r.status_code != 200:
            raise AXLUnavailable(f"topology status {r.status_code}: {r.text[:200]}")
        data = r.json()
        # Real AXL response shape: { our_ipv6, our_public_key, peers: [{public_key, uri, ...}], tree }
        peer_ids = [p.get("public_key", "") for p in (data.get("peers") or [])]
        return AXLTopology(
            self_peer_id=data.get("our_public_key", ""),
            connected_peers=[p for p in peer_ids if p],
            raw=data,
        )

    async def send(
        self,
        to_peer_id: str,
        to_agent: str,
        msg_type: str,
        body: dict,
    ) -> AXLMessage:
        """Send a structured A2A message to another agent's AXL peer."""
        msg = AXLMessage(
            msg_id=str(uuid.uuid4()),
            from_peer="",  # filled in by AXL on the other side
            from_agent=self.agent_id,
            to_agent=to_agent,
            type=msg_type,
            body=body,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        payload = json.dumps(
            {
                "msg_id": msg.msg_id,
                "from_agent": msg.from_agent,
                "to_agent": msg.to_agent,
                "type": msg.type,
                "body": msg.body,
                "timestamp": msg.timestamp,
            }
        ).encode("utf-8")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{self.base_url}/send",
                    content=payload,
                    headers={
                        "X-Destination-Peer-Id": to_peer_id,
                        "Content-Type": "application/json",
                    },
                )
        except httpx.HTTPError as e:
            raise AXLUnavailable(f"send failed: {e}") from e
        if r.status_code >= 300:
            raise AXLUnavailable(f"send status {r.status_code}: {r.text[:200]}")
        return msg

    async def recv(self, timeout_sec: float = 30.0) -> Optional[AXLMessage]:
        """Poll for the next inbound message. Returns None on timeout/no-message."""
        try:
            async with httpx.AsyncClient(timeout=timeout_sec + 5.0) as client:
                r = await client.get(f"{self.base_url}/recv")
        except httpx.HTTPError as e:
            raise AXLUnavailable(f"recv failed: {e}") from e

        if r.status_code == 204:  # no message
            return None
        if r.status_code != 200:
            raise AXLUnavailable(f"recv status {r.status_code}: {r.text[:200]}")

        from_peer = r.headers.get("X-From-Peer-Id", "")
        try:
            envelope = json.loads(r.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise AXLUnavailable(f"received malformed envelope: {e}") from e

        return AXLMessage(
            msg_id=envelope.get("msg_id", ""),
            from_peer=from_peer,
            from_agent=envelope.get("from_agent", ""),
            to_agent=envelope.get("to_agent", ""),
            type=envelope.get("type", ""),
            body=envelope.get("body", {}),
            timestamp=envelope.get("timestamp", ""),
        )
