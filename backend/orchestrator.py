"""Demo orchestration — runs the full fake lifecycle with realistic delays."""

import asyncio
import uuid

from backend.state import demo_state
from backend.schemas.agent import AgentStatus
from backend.schemas.task import Task, TaskStatus
from backend.schemas.events import EventType

# Fake tx hashes for the demo
FAKE_TX = "0x" + "a1b2c3d4e5f6" * 5 + "abcd"
FAKE_REWARD_TX = "0x" + "f6e5d4c3b2a1" * 5 + "ef01"
FAKE_SWAP_TX = "0x" + "1234567890ab" * 5 + "cdef"
FAKE_MEMORY_KEY = "0g://agentfi-city/memory/executor-001/task-001"


async def _step(delay: float = 1.5):
    """Wait between steps for a natural demo pace."""
    await asyncio.sleep(delay)


async def run_demo() -> None:
    """Execute the full demo lifecycle, emitting events at each step."""

    state = demo_state
    state.demo_id = f"demo-{uuid.uuid4().hex[:8]}"
    state.is_running = True

    task = Task(
        id="task-001",
        title="Analyze ETH market trend",
        description="Research recent ETH price movements and sentiment, then produce a short summary report.",
        reward_token="ETH",
        reward_amount="0.01",
        status=TaskStatus.CREATED,
    )
    state.task = task

    # --- Step 1: Task created ---
    state.emit_event(
        EventType.TASK_CREATED,
        "System",
        f"Task created: {task.title} (reward: {task.reward_amount} {task.reward_token})",
        {"task_id": task.id, "reward": task.reward_amount},
    )
    await _step()

    # --- Step 2: Planner broadcasts via AXL ---
    state.set_agent_status("planner-001", AgentStatus.LISTENING)
    state.emit_event(
        EventType.AXL_MESSAGE,
        "Planner",
        "Broadcasting task announcement via AXL peer-to-peer network",
        {"from": "planner-001", "to": "broadcast", "msg_type": "TASK_ANNOUNCEMENT"},
    )
    task.status = TaskStatus.BROADCASTED
    await _step()

    # --- Step 3: Researcher receives and decides to join ---
    state.set_agent_status("researcher-001", AgentStatus.LISTENING)
    state.emit_event(
        EventType.AXL_MESSAGE,
        "Researcher",
        "Received task announcement via AXL",
        {"from": "planner-001", "to": "researcher-001"},
    )
    await _step(1.0)

    state.set_agent_status("researcher-001", AgentStatus.NEGOTIATING)
    state.emit_event(
        EventType.AGENT_DECISION,
        "Researcher",
        'Decision: JOIN — task matches research capability. Reason: "I can summarize recent market conditions."',
        {"agent_id": "researcher-001", "decision": "join", "capability": "research"},
    )
    await _step(0.8)

    state.emit_event(
        EventType.AXL_MESSAGE,
        "Researcher",
        "Sent JOIN_PROPOSAL to Planner via AXL",
        {"from": "researcher-001", "to": "planner-001", "msg_type": "JOIN_PROPOSAL"},
    )
    task.status = TaskStatus.TEAM_FORMING
    await _step()

    # --- Step 4: Executor receives and decides to join ---
    state.set_agent_status("executor-001", AgentStatus.LISTENING)
    state.emit_event(
        EventType.AXL_MESSAGE,
        "Executor",
        "Received task announcement via AXL",
        {"from": "planner-001", "to": "executor-001"},
    )
    await _step(1.0)

    state.set_agent_status("executor-001", AgentStatus.NEGOTIATING)
    state.emit_event(
        EventType.AGENT_DECISION,
        "Executor",
        'Decision: JOIN — reward exists and task requires execution. Reason: "Will execute and swap 30% of reward."',
        {"agent_id": "executor-001", "decision": "join", "capability": "execution"},
    )
    await _step(0.8)

    state.emit_event(
        EventType.AXL_MESSAGE,
        "Executor",
        "Sent JOIN_PROPOSAL to Planner via AXL",
        {"from": "executor-001", "to": "planner-001", "msg_type": "JOIN_PROPOSAL"},
    )
    await _step()

    # --- Step 5: Planner forms team ---
    state.emit_event(
        EventType.AGENT_DECISION,
        "Planner",
        "Received 2 join proposals. Forming team: [Researcher, Executor]",
        {"team": ["researcher-001", "executor-001"]},
    )
    task.status = TaskStatus.TEAM_FORMED
    task.participants = ["researcher-001", "executor-001"]
    await _step(0.8)

    state.emit_event(
        EventType.AXL_MESSAGE,
        "Planner",
        "Sent TEAM_CONFIRMED to all participants via AXL",
        {"from": "planner-001", "to": "broadcast", "msg_type": "TEAM_CONFIRMED"},
    )
    await _step()

    # --- Step 6: Onchain task creation ---
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        f"Creating task onchain via TaskMarket.sol",
        {"action": "createTask", "tx_hash": FAKE_TX[:20] + "..."},
    )
    await _step(2.0)

    task.onchain_task_id = 0
    task.tx_hashes.append(FAKE_TX)
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        f"Task created onchain — taskId: 0, tx: {FAKE_TX[:20]}...",
        {"task_id_onchain": 0, "tx_hash": FAKE_TX},
    )
    await _step()

    # --- Step 7: Agents join onchain ---
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        "Researcher and Executor joining task onchain",
        {"action": "joinTask"},
    )
    await _step(1.5)

    # --- Step 8: Task execution ---
    task.status = TaskStatus.EXECUTING
    state.set_agent_status("researcher-001", AgentStatus.WORKING)
    state.set_agent_status("executor-001", AgentStatus.WORKING)
    state.emit_event(
        EventType.AGENT_DECISION,
        "Researcher",
        "Executing research: analyzing ETH market trend...",
        {"agent_id": "researcher-001"},
    )
    await _step(2.0)

    state.emit_event(
        EventType.AGENT_DECISION,
        "Researcher",
        'Research complete: "ETH sentiment appears cautiously optimistic with increased institutional inflows."',
        {"agent_id": "researcher-001", "output": "ETH sentiment cautiously optimistic"},
    )
    await _step()

    state.emit_event(
        EventType.AGENT_DECISION,
        "Executor",
        "Compiled final report and submitted task completion",
        {"agent_id": "executor-001"},
    )
    task.status = TaskStatus.COMPLETED
    await _step()

    # --- Step 9: Complete task onchain ---
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        "Marking task as completed onchain",
        {"action": "completeTask"},
    )
    await _step(1.5)

    # --- Step 10: Distribute reward ---
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        f"Distributing reward: 0.005 ETH per agent",
        {"action": "distributeReward", "per_agent": "0.005 ETH"},
    )
    await _step(2.0)

    task.tx_hashes.append(FAKE_REWARD_TX)
    task.status = TaskStatus.SETTLED
    state.set_agent_status("researcher-001", AgentStatus.PAID)
    state.set_agent_status("executor-001", AgentStatus.PAID)
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        f"Reward distributed — tx: {FAKE_REWARD_TX[:20]}...",
        {"tx_hash": FAKE_REWARD_TX},
    )
    await _step()

    # --- Step 11: Uniswap quote ---
    state.emit_event(
        EventType.UNISWAP_QUOTE,
        "Executor",
        "Requesting Uniswap quote: swap 30% of reward (0.0015 ETH → USDC)",
        {"from_token": "ETH", "to_token": "USDC", "amount": "0.0015"},
    )
    await _step(1.5)

    state.emit_event(
        EventType.UNISWAP_QUOTE,
        "Uniswap",
        "Quote received: 0.0015 ETH → 3.42 USDC (rate: 2280 USDC/ETH)",
        {"quote": "3.42 USDC", "rate": "2280"},
    )
    await _step()

    # --- Step 12: Uniswap swap execution ---
    state.emit_event(
        EventType.UNISWAP_SWAP,
        "Executor",
        "Executing swap via Uniswap API...",
        {"action": "swap"},
    )
    await _step(2.0)

    task.tx_hashes.append(FAKE_SWAP_TX)
    task.status = TaskStatus.SWAPPED
    state.set_agent_status("executor-001", AgentStatus.SWAPPED)
    state.emit_event(
        EventType.UNISWAP_SWAP,
        "Uniswap",
        f"Swap executed — tx: {FAKE_SWAP_TX[:20]}...",
        {"tx_hash": FAKE_SWAP_TX},
    )
    await _step()

    # --- Step 13: Save memory to 0G Storage ---
    state.emit_event(
        EventType.MEMORY_WRITE,
        "Executor",
        "Saving agent memory and task result to 0G Storage...",
        {"agent_id": "executor-001", "task_id": "task-001"},
    )
    await _step(1.5)

    memory_obj = {
        "agent_id": "executor-001",
        "task_id": "task-001",
        "decision": "Joined because expected reward was positive and required capability matched executor role.",
        "reward_received": "0.005 ETH",
        "financial_action": "Swapped 30% of reward (0.0015 ETH) to 3.42 USDC",
        "research_summary": "ETH sentiment cautiously optimistic with increased institutional inflows.",
    }
    task.status = TaskStatus.MEMORY_SAVED
    state.emit_event(
        EventType.MEMORY_WRITE,
        "0G Storage",
        f"Memory saved — key: {FAKE_MEMORY_KEY}",
        {"storage_key": FAKE_MEMORY_KEY, "memory": memory_obj},
    )
    await _step()

    # --- Done ---
    state.emit_event(
        EventType.DONE,
        "System",
        "Demo completed. Full lifecycle: Task → Coordinate → Execute → Settle → Swap → Remember",
    )
    state.is_running = False
