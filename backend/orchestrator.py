"""Demo orchestration — runs the full lifecycle.

Contract steps switch between real onchain calls (via TaskMarketService) and
fake tx hashes based on the USE_REAL_CONTRACT config flag. Uniswap and 0G
steps remain fake until those services are wired in later commits.
"""

import asyncio
import uuid

from backend.state import demo_state
from backend.schemas.agent import AgentStatus
from backend.schemas.task import Task, TaskStatus
from backend.schemas.events import EventType
from backend.services.contract_runtime import get_contract_runtime
from backend.services import llm_service

# Fake tx hashes used when real-contract mode is off
FAKE_TX = "0x" + "a1b2c3d4e5f6" * 5 + "abcd"
FAKE_REWARD_TX = "0x" + "f6e5d4c3b2a1" * 5 + "ef01"
FAKE_SWAP_TX = "0x" + "1234567890ab" * 5 + "cdef"
FAKE_MEMORY_KEY = "0g://agentfi-city/memory/executor-001/task-001"

REWARD_ETH = 0.01


async def _step(delay: float = 1.5):
    """Wait between steps for a natural demo pace."""
    await asyncio.sleep(delay)


async def run_demo() -> None:
    """Execute the full demo lifecycle, emitting events at each step."""

    state = demo_state
    state.demo_id = f"demo-{uuid.uuid4().hex[:8]}"
    state.is_running = True

    # Resolve real-contract runtime (None if disabled or no deployment file)
    runtime = get_contract_runtime()
    if runtime:
        # Sync agent wallet addresses to the real ones from the runtime
        state.get_agent("planner-001").wallet_address = runtime.planner.address
        state.get_agent("researcher-001").wallet_address = runtime.researcher.address
        state.get_agent("executor-001").wallet_address = runtime.executor.address
        state.emit_event(
            EventType.AGENT_DECISION,
            "System",
            f"Real-contract mode: TaskMarket at {runtime.service.deployment.address} on chain {runtime.service.deployment.chain_id}",
            {
                "address": runtime.service.deployment.address,
                "chain_id": runtime.service.deployment.chain_id,
                "network": runtime.service.deployment.network,
            },
        )

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

    # --- Step 4a: Critic receives and decides to join ---
    state.set_agent_status("critic-001", AgentStatus.LISTENING)
    state.emit_event(
        EventType.AXL_MESSAGE,
        "Critic",
        "Received task announcement via AXL",
        {"from": "planner-001", "to": "critic-001"},
    )
    await _step(1.0)

    state.set_agent_status("critic-001", AgentStatus.NEGOTIATING)
    state.emit_event(
        EventType.AGENT_DECISION,
        "Critic",
        'Decision: JOIN — task output requires validation. Reason: "I will fact-check the Researcher\'s output before settlement."',
        {"agent_id": "critic-001", "decision": "join", "capability": "validation"},
    )
    await _step(0.8)

    state.emit_event(
        EventType.AXL_MESSAGE,
        "Critic",
        "Sent JOIN_PROPOSAL to Planner via AXL",
        {"from": "critic-001", "to": "planner-001", "msg_type": "JOIN_PROPOSAL"},
    )
    await _step()

    # --- Step 4b: Executor receives and decides to join ---
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
        "Received 3 join proposals. Forming team: [Researcher, Critic, Executor]",
        {"team": ["researcher-001", "critic-001", "executor-001"]},
    )
    task.status = TaskStatus.TEAM_FORMED
    task.participants = ["researcher-001", "critic-001", "executor-001"]
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
        "Creating task onchain via TaskMarket.sol",
        {"action": "createTask"},
    )

    if runtime:
        reward_wei = runtime.service.w3.to_wei(REWARD_ETH, "ether")
        create_tx, onchain_id = await asyncio.to_thread(
            runtime.service.create_task,
            runtime.task_creator.private_key,
            task.description,
            reward_wei,
        )
    else:
        await _step(2.0)
        create_tx, onchain_id = FAKE_TX, 0

    task.onchain_task_id = onchain_id
    task.tx_hashes.append(create_tx)
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        f"Task created onchain — taskId: {onchain_id}, tx: {create_tx[:20]}...",
        {"task_id_onchain": onchain_id, "tx_hash": create_tx},
    )
    await _step()

    # --- Step 7: Agents join onchain ---
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        "Researcher, Critic, and Executor joining task onchain",
        {"action": "joinTask"},
    )

    if runtime:
        researcher_join_tx = await asyncio.to_thread(
            runtime.service.join_task, runtime.researcher.private_key, onchain_id
        )
        critic_join_tx = await asyncio.to_thread(
            runtime.service.join_task, runtime.critic.private_key, onchain_id
        )
        executor_join_tx = await asyncio.to_thread(
            runtime.service.join_task, runtime.executor.private_key, onchain_id
        )
        task.tx_hashes.extend([researcher_join_tx, critic_join_tx, executor_join_tx])
        for agent_id, tx in [
            ("researcher-001", researcher_join_tx),
            ("critic-001", critic_join_tx),
            ("executor-001", executor_join_tx),
        ]:
            state.emit_event(
                EventType.CONTRACT_TX,
                "Contract",
                f"{agent_id} joined — tx: {tx[:20]}...",
                {"agent": agent_id, "tx_hash": tx},
            )
    else:
        await _step(1.5)

    # --- Step 8: Task execution ---
    task.status = TaskStatus.EXECUTING
    state.set_agent_status("researcher-001", AgentStatus.WORKING)
    state.set_agent_status("critic-001", AgentStatus.LISTENING)
    state.set_agent_status("executor-001", AgentStatus.WORKING)
    state.emit_event(
        EventType.AGENT_DECISION,
        "Researcher",
        "Executing research: analyzing ETH market trend...",
        {"agent_id": "researcher-001"},
    )
    await _step(2.0)

    research_output = "ETH sentiment appears cautiously optimistic with increased institutional inflows."
    state.emit_event(
        EventType.AGENT_DECISION,
        "Researcher",
        f'Research complete: "{research_output}"',
        {"agent_id": "researcher-001", "output": research_output},
    )
    await _step()

    # --- Step 8b: Critic validates Researcher output ---
    state.set_agent_status("researcher-001", AgentStatus.LISTENING)
    state.set_agent_status("critic-001", AgentStatus.REVIEWING)
    state.emit_event(
        EventType.AXL_MESSAGE,
        "Researcher",
        "Sent OUTPUT_FOR_REVIEW to Critic via AXL",
        {
            "from": "researcher-001",
            "to": "critic-001",
            "msg_type": "OUTPUT_FOR_REVIEW",
            "output": research_output,
        },
    )
    await _step(1.0)

    state.emit_event(
        EventType.CRITIC_REVIEW,
        "Critic",
        "Validating Researcher output via LLM call...",
        {
            "agent_id": "critic-001",
            "task_description": task.description,
            "output_under_review": research_output,
        },
    )

    critique = await llm_service.validate_research(task.description, research_output)
    verdict = "APPROVED" if critique.approved else "REJECTED"
    state.emit_event(
        EventType.CRITIC_REVIEW,
        "Critic",
        f"{verdict} (model={critique.model}, confidence={critique.confidence}): {critique.reason}",
        {
            "agent_id": "critic-001",
            "verdict": {
                "approved": critique.approved,
                "reason": critique.reason,
                "confidence": critique.confidence,
            },
            "model": critique.model,
            "raw_response": critique.raw_response,
        },
    )
    await _step(0.8)

    msg_type = "APPROVE" if critique.approved else "REJECT"
    state.emit_event(
        EventType.AXL_MESSAGE,
        "Critic",
        f"Sent {msg_type} to Executor via AXL",
        {"from": "critic-001", "to": "executor-001", "msg_type": msg_type},
    )
    state.set_agent_status("critic-001", AgentStatus.IDLE)
    await _step()

    state.emit_event(
        EventType.AGENT_DECISION,
        "Executor",
        f"Compiled final report and submitted task completion (Critic {msg_type.lower()}d)",
        {"agent_id": "executor-001", "critic_approved": critique.approved},
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

    if runtime:
        complete_tx = await asyncio.to_thread(
            runtime.service.complete_task,
            runtime.task_creator.private_key,
            task.onchain_task_id,
        )
        task.tx_hashes.append(complete_tx)
        state.emit_event(
            EventType.CONTRACT_TX,
            "Contract",
            f"Task completed onchain — tx: {complete_tx[:20]}...",
            {"tx_hash": complete_tx},
        )
    else:
        await _step(1.5)

    # --- Step 10: Distribute reward ---
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        "Distributing reward via TaskMarket.distributeReward()",
        {"action": "distributeReward"},
    )

    if runtime:
        reward_tx, per_agent_wei = await asyncio.to_thread(
            runtime.service.distribute_reward,
            runtime.task_creator.private_key,
            task.onchain_task_id,
        )
        per_agent_eth = float(runtime.service.w3.from_wei(per_agent_wei, "ether"))
    else:
        await _step(2.0)
        reward_tx = FAKE_REWARD_TX
        per_agent_eth = REWARD_ETH / 3

    task.tx_hashes.append(reward_tx)
    task.status = TaskStatus.SETTLED
    state.set_agent_status("researcher-001", AgentStatus.PAID)
    state.set_agent_status("critic-001", AgentStatus.PAID)
    state.set_agent_status("executor-001", AgentStatus.PAID)
    state.emit_event(
        EventType.CONTRACT_TX,
        "Contract",
        f"Reward distributed: {per_agent_eth} ETH/agent — tx: {reward_tx[:20]}...",
        {"tx_hash": reward_tx, "per_agent_eth": per_agent_eth},
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
