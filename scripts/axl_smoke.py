"""Smoke test: prove real AXL communication between two separate nodes.

Run AFTER the AXL binary is built and at least the planner+researcher nodes
are running (see infra/axl/README.md). Sends one message planner→researcher
and prints the round-trip.

Usage:
  # In one shell, run two AXL nodes per the README, then:
  python scripts/axl_smoke.py \\
    --planner-url http://localhost:7001 \\
    --researcher-url http://localhost:7002 \\
    --researcher-peer-id <peer id printed by researcher node on startup>

The peer ID is whatever the researcher's AXL node prints at startup or returns
from GET /topology.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from backend.services.axl_service import AXLClient, AXLUnavailable


async def main(planner_url: str, researcher_url: str, researcher_peer_id: str):
    planner = AXLClient(planner_url, agent_id="planner-001")
    researcher = AXLClient(researcher_url, agent_id="researcher-001")

    # Sanity: both nodes reachable
    try:
        p_topo = await planner.topology()
        r_topo = await researcher.topology()
    except AXLUnavailable as e:
        print(f"FAIL: AXL unreachable — {e}")
        sys.exit(1)

    print(f"planner    peer_id: {p_topo.self_peer_id}  peers: {len(p_topo.connected_peers)}")
    print(f"researcher peer_id: {r_topo.self_peer_id}  peers: {len(r_topo.connected_peers)}")

    if not researcher_peer_id:
        researcher_peer_id = r_topo.self_peer_id
        print(f"(using researcher peer_id from topology: {researcher_peer_id})")

    # Send: planner -> researcher
    sent = await planner.send(
        to_peer_id=researcher_peer_id,
        to_agent="researcher-001",
        msg_type="TASK_ANNOUNCEMENT",
        body={"task": "Analyze ETH market trend", "reward": "0.01 ETH"},
    )
    print(f"\nSent  msg_id={sent.msg_id} from=planner-001 to=researcher-001")

    # Receive: researcher polls
    received = await researcher.recv(timeout_sec=10.0)
    if received is None:
        print("FAIL: researcher timed out waiting for message")
        sys.exit(2)

    print(f"Recv  msg_id={received.msg_id} from_peer={received.from_peer[:16]}...")
    print(f"      type={received.type} body={received.body}")

    if received.msg_id != sent.msg_id:
        print(
            f"FAIL: msg_id mismatch — sent {sent.msg_id} got {received.msg_id}"
        )
        sys.exit(3)

    print("\nOK — real AXL round trip across two separate nodes.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--planner-url", default="http://localhost:7001")
    ap.add_argument("--researcher-url", default="http://localhost:7002")
    ap.add_argument("--researcher-peer-id", default="")
    args = ap.parse_args()

    asyncio.run(main(args.planner_url, args.researcher_url, args.researcher_peer_id))
