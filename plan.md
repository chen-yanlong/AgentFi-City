# AgentFi City — Full Development Plan

## 0. Project Summary

**AgentFi City** is an onchain autonomous agent economy.

The project demonstrates a group of AI agents that can:

1. discover tasks,
2. communicate peer-to-peer,
3. form a team,
4. execute a task,
5. receive onchain rewards,
6. and perform financial actions such as token swaps.

The goal is not to build a production-ready agent economy, but to build a strong hackathon MVP that clearly demonstrates:

* autonomous agent behavior,
* decentralized agent-to-agent communication,
* onchain task settlement,
* token swap / financial execution,
* and persistent memory.

The project targets three main bounties:

1. **0G — Autonomous Agents**
2. **Gensyn — AXL**
3. **Uniswap — API Integration**

The 0G bounty specifically rewards autonomous agents, swarms, persistent memory through 0G Storage, and integration with 0G Compute; the Gensyn bounty requires meaningful use of AXL for peer-to-peer agent communication across separate nodes; the Uniswap bounty rewards agents that use the Uniswap API for real onchain value exchange. 

---

# 1. Core Product Idea

## Product Name

**AgentFi City**

## One-liner

> A decentralized onchain economy where autonomous AI agents coordinate peer-to-peer, complete tasks, earn rewards, and manage assets.

## Longer Description

AgentFi City is a **4-agent swarm** (Planner + Researcher + Critic + Executor) where each agent behaves like an onchain economic actor.
Each agent has:

* a role,
* a wallet,
* persistent memory on 0G Storage (read AND write — decisions are informed by past outcomes),
* peer-to-peer communication via AXL (separate processes, no central broker),
* LLM-based decision-making (with at least one call routed through 0G Compute).

Agents coordinate through AXL P2P, the Critic validates Researcher output before settlement, and rewards settle onchain through a smart contract.

After receiving rewards, agents can use the Uniswap API to perform token swaps, demonstrating that they are not just chatbots, but financial actors capable of operating onchain.

---

# 2. Bounty Strategy

## 2.1 0G — Autonomous Agents & Swarms

### Track name (corrected)

We target the **”Best Autonomous Agents, Swarms & iNFT Innovations”** track ($7,500 pool, **5 × $1,500** slots). NOT the framework track — that's for OpenClaw extensions/forks/agent-brain libraries.

### What the bounty wants

The bounty rewards:

* specialist agent swarms — the bounty literally names “planner + researcher + critic + executor”,
* shared 0G Storage memory using both KV (real-time state) and Log (history),
* coordinated inference on 0G Compute with a live model (queried at runtime via `broker.inference.listService()` — the catalog changes, do not hard-code names),
* persistent context that affects future behavior (not write-only memory),
* clear explanation of how agents communicate and coordinate.

### How AgentFi City fits

AgentFi City is a **4-agent swarm**:

* **Planner** — broadcasts tasks, forms teams
* **Researcher** — produces research output
* **Critic** — validates Researcher output before settlement (added to match the bounty's literal pattern)
* **Executor** — submits completion, swaps reward

Each agent:

* reads its past memories from 0G Storage Log before deciding to join,
* writes new decisions/results to 0G Storage (KV for live state, Log for history),
* uses 0G Compute for at least one reasoning call.

### Minimum required implementation (REQUIRED — not optional)

For MVP:

* **0G Storage write**: save agent memory and task history.
* **0G Storage read-back**: at least one agent decision must be informed by previously-saved memory. The decision JSON must reference the past memory it read.
* **0G Compute call**: at least one decision must use a live model on 0G Compute. Query the available models at runtime via `broker.inference.listService()` — do not hard-code model names. Show the request/response (including the resolved model name) in the UI.
* **4 agents**: Planner, Researcher, Critic, Executor — each running as a separate process.
* **Two-run demo**: first run with empty memory, second run shows agents making different/more confident decisions because of read-back.
* **Contract deployed on 0G testnet** with explorer link in README.

### Nice-to-have

* Mint agent identity as iNFT (ERC-7857) — high time cost, park unless ahead of schedule.
* Reputation score that evolves with completed tasks, stored in 0G Storage KV.
* Self-fact-checking — Critic uses a second 0G Compute call to verify Researcher's output.

---

## 2.2 Gensyn — AXL

### What the bounty wants

Gensyn’s AXL bounty requires real use of AXL for inter-agent or inter-node communication. It explicitly says projects must demonstrate communication across separate AXL nodes, not just in-process communication. AXL provides encrypted decentralized communication, routing, peer discovery, and supports MCP and A2A. 

AXL documentation describes it as a peer-to-peer network node for agents and AI applications, with structured agent-to-agent communication support. ([Gensyn][1])

### How AgentFi City fits

AgentFi City uses AXL as the communication layer between agents.

Example:

```txt
Planner Agent → broadcasts task
Researcher Agent → replies with capability
Executor Agent → confirms execution
Planner Agent → confirms team formation
```

### Reference implementation

Mirror the pattern of Gensyn's **Collaborative Autoresearch Demo** (`github.com/gensyn-ai/collaborative-autoresearch-demo`) — researchers collaborating via AXL, which maps directly to our use case.

### Minimum required implementation

For MVP:

* Run **all 4 agents as separate processes** (Planner, Researcher, Critic, Executor) — each with its own AXL node.
* All inter-agent messages flow through AXL — no centralized broker, no in-process shortcuts.
* Use A2A-style structured message schema.
* Frontend shows: peer discovery (which nodes connected), live AXL message stream, message direction (from→to).
* Logs prove this is real P2P, not faked.

### Nice-to-have

* Peer discovery screen showing AXL mesh topology.
* MCP-style structured tool calls between agents (the bounty mentions MCP support).
* Encrypted message inspection panel showing AXL's E2E encryption.

---

## 2.3 Uniswap — API Integration

### What the bounty wants

The Uniswap bounty asks builders to integrate the Uniswap API and give agents the ability to swap and settle value onchain. The bounty also requires a `FEEDBACK.md` file in the repo root explaining the builder experience with the Uniswap API. 

Uniswap’s developer docs describe APIs for integrating swaps and liquidity features, and the swapping API provides quote and transaction-building services. ([Uniswap Developers][2])

### How AgentFi City fits

After agents complete a task and receive rewards, one agent performs a swap.

Example:

```txt
Executor Agent receives USDC reward
Executor Agent decides to convert 30% of reward to ETH
Uniswap API provides quote and transaction
Agent wallet executes swap
```

### Chain and API commitment

* **Chain**: **Base Sepolia** (testnet that supports Uniswap with reliable RPC). Backup: Sepolia.
* **API**: Uniswap **Trading API** at `https://trade-api.gateway.uniswap.org/v1` — `/quote` + `/swap` endpoints.
* Smart contract deploys to **two networks**: Base Sepolia (for Uniswap visibility) and 0G testnet (for 0G bounty visibility).

### Minimum required implementation

For MVP:

* Use Uniswap Trading API to get a real quote (`/quote` endpoint).
* **Execute the swap** with the agent's wallet — actual onchain transaction, not just "show prepared tx" (that's the demo-day fallback only).
* Show quote payload, tx hash, and **clickable Etherscan/Basescan link** in frontend.
* `FEEDBACK.md` must be **substantive** (10+ specific bullets per section, not skeleton). It's graded.

### Nice-to-have

* Agent chooses swap percentage based on simple strategy.
* Compare two routes / tokens.
* Risk guardrails: max slippage, max trade size, testnet-only mode.

---

# 3. MVP Scope

## The MVP should prove one full lifecycle (run twice)

```txt
Task Created
→ Agents read past memory from 0G Storage
→ Agents Coordinate via AXL
→ Team Formed
→ Researcher Produces Output
→ Critic Validates via 0G Compute
→ Task Executed
→ Reward Settled Onchain
→ Agent Swaps Token via Uniswap
→ Memory Saved to 0G Storage
```

**Run the demo twice during the pitch:**

1. **Run 1 (cold start)**: empty memory, agents make baseline decisions.
2. **Run 2 (memory-informed)**: agents read Run 1 memories, decisions cite past outcomes, confidence shifts. This is the bounty-critical proof that memory affects behavior.

This flow is more important than building a complex autonomous economy.

## What must be real

These should be real, not fake:

1. Smart contract deployment.
2. At least one onchain transaction.
3. AXL message passing between separate nodes.
4. Uniswap API quote.
5. 0G Storage write or read.

## What can be partially mocked

These can be simplified:

1. Actual task content.
2. AI reasoning complexity.
3. Researcher’s output.
4. Executor’s actual work.
5. Full autonomy.

The demo can be semi-orchestrated, as long as the key infra integrations are real.

---

# 4. Recommended Architecture

## High-level Architecture

```txt
┌────────────────────────────┐
│        Frontend UI          │
│   Next.js + Tailwind        │
└─────────────┬──────────────┘
              │
              │ REST / SSE / WebSocket
              ↓
┌────────────────────────────┐
│      FastAPI Backend        │
│   Demo Orchestrator         │
└─────────────┬──────────────┘
              │
 ┌────────┬───┴───┬────────┐
 ↓        ↓       ↓        ↓
Planner Researcher Critic Executor
Agent    Agent     Agent  Agent
Node     Node      Node   Node
 ↓        ↓       ↓        ↓
┌────────────────────────────┐
│        Gensyn AXL           │
│ P2P agent communication     │
└────────────────────────────┘
              │
              ↓
┌────────────────────────────┐
│      Smart Contract         │
│      TaskMarket.sol         │
└────────────────────────────┘
              │
              ↓
┌────────────────────────────┐
│       Uniswap API           │
│ quote / swap execution      │
└────────────────────────────┘
              │
              ↓
┌────────────────────────────┐
│        0G Storage           │
│ memory / task history       │
└────────────────────────────┘
```

---

# 5. App Type Decision

## Recommended app type

Build a **frontend demo app + backend orchestrator + agent CLI nodes**.

Do **not** build only a CLI.
Do **not** build only a frontend.
Do **not** build a fully decentralized production app.

The hackathon demo needs a clear visual story, so the frontend is important.

## Why not CLI only?

CLI is easier, but judges may not immediately understand the product value.
AXL and backend logs may look too technical.

## Why frontend matters

Frontend helps show:

* agents as actors,
* message flow,
* task lifecycle,
* transaction hashes,
* reward distribution,
* token swap,
* memory storage.

## Why backend matters

The backend keeps the demo stable.
A fully autonomous agent flow may fail during demo due to timing, networking, API, or wallet issues.

The backend should orchestrate the demo while still allowing real agent processes and real infra integrations.

---

# 6. Tech Stack

## Frontend

Use:

```txt
Next.js
TypeScript
Tailwind CSS
shadcn/ui optional
viem or ethers
```

Main features:

* dashboard UI,
* start demo button,
* agent cards,
* task timeline,
* live event log,
* transaction panel,
* memory panel.

---

## Backend

Use:

```txt
FastAPI
Python
Pydantic
uvicorn
httpx
websockets or Server-Sent Events
```

Main features:

* trigger demo flow,
* manage task state,
* collect logs,
* expose API to frontend,
* interface with agents,
* call contract service,
* call Uniswap service,
* call 0G service.

---

## Agents

Use:

```txt
Python scripts
```

Example agents:

```txt
planner_agent.py
researcher_agent.py
executor_agent.py
```

Each agent should run as a separate process.

Each agent should have:

```txt
agent_id
name
role
wallet_address
private_key from env
memory
AXL peer address
decision_policy
```

---

## Smart Contract

Use:

```txt
Solidity
Foundry or Hardhat
```

I recommend **Foundry** if you are comfortable with Solidity.
Use **Hardhat** if you want easier TypeScript integration.

---

## Chain

Pick one chain based on hackathon requirements and compatibility.

Priority:

1. **0G Chain**, if contract deployment is stable and required for 0G.
2. Ethereum-compatible testnet, if Uniswap API support is easier.
3. Local Anvil only for early development, not final demo.

The bounty requirements mention contract deployment addresses and 0G integration for 0G submissions, so the final demo should include deployed addresses where possible. 

---

# 7. Repository Structure

```txt
agentfi-city/
│
├── README.md
├── FEEDBACK.md
├── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── AgentCard.tsx
│   │   ├── TaskTimeline.tsx
│   │   ├── EventLog.tsx
│   │   ├── TransactionPanel.tsx
│   │   └── MemoryPanel.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts
│   └── package.json
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── state.py
│   ├── schemas/
│   │   ├── agent.py
│   │   ├── task.py
│   │   └── events.py
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── planner_agent.py
│   │   ├── researcher_agent.py
│   │   ├── critic_agent.py
│   │   └── executor_agent.py
│   ├── services/
│   │   ├── axl_service.py
│   │   ├── contract_service.py
│   │   ├── uniswap_service.py
│   │   ├── og_storage_service.py
│   │   └── llm_service.py
│   ├── routes/
│   │   ├── demo.py
│   │   ├── events.py
│   │   └── health.py
│   └── requirements.txt
│
├── contracts/
│   ├── foundry.toml
│   ├── src/
│   │   └── TaskMarket.sol
│   ├── script/
│   │   ├── Deploy.s.sol
│   │   └── DemoFund.s.sol
│   └── test/
│       └── TaskMarket.t.sol
│
├── scripts/
│   ├── run_all.sh
│   ├── run_agents.sh
│   ├── seed_demo_wallets.sh
│   └── demo_reset.sh
│
└── docs/
    ├── architecture.md
    ├── demo-script.md
    ├── bounty-mapping.md
    └── troubleshooting.md
```

---

# 8. Data Model

## Agent

```ts
type Agent = {
  id: string;
  name: string;
  role: "planner" | "researcher" | "critic" | "executor";
  walletAddress: string;
  status: "idle" | "listening" | "negotiating" | "working" | "paid" | "swapped";
  memoryKey?: string;
};
```

## Task

```ts
type Task = {
  id: string;
  onchainTaskId?: number;
  title: string;
  description: string;
  rewardToken: string;
  rewardAmount: string;
  status:
    | "created"
    | "broadcasted"
    | "team_forming"
    | "team_formed"
    | "executing"
    | "completed"
    | "settled"
    | "swapped"
    | "memory_saved";
  participants: string[];
  txHashes: string[];
};
```

## Event Log

```ts
type DemoEvent = {
  id: string;
  timestamp: string;
  source: string;
  type:
    | "task_created"
    | "axl_message"
    | "agent_decision"
    | "contract_tx"
    | "uniswap_quote"
    | "uniswap_swap"
    | "memory_read"
    | "memory_write"
    | "compute_call"
    | "critic_review"
    | "error";
  message: string;
  metadata?: Record<string, unknown>;
};
```

## Agent Memory

```json
{
  "agent_id": "executor-001",
  "task_id": "task-001",
  "decision": "Joined the task because expected reward was positive and required capability matched executor role.",
  "reward_received": "10 USDC",
  "financial_action": "Swapped 30% of USDC reward to ETH",
  "timestamp": "2026-05-01T12:00:00Z"
}
```

---

# 9. Smart Contract Design

## Contract Name

```solidity
TaskMarket.sol
```

## Purpose

The contract manages task creation, team participation, task completion, and reward distribution.

## Minimal Solidity Interface

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract TaskMarket {
    enum TaskStatus {
        Created,
        InProgress,
        Completed,
        Settled
    }

    struct Task {
        uint256 id;
        address creator;
        string description;
        uint256 reward;
        TaskStatus status;
        address[] participants;
    }

    uint256 public nextTaskId;
    mapping(uint256 => Task) public tasks;
    mapping(uint256 => mapping(address => bool)) public hasJoined;

    event TaskCreated(uint256 indexed taskId, address indexed creator, string description, uint256 reward);
    event TaskJoined(uint256 indexed taskId, address indexed agent);
    event TaskCompleted(uint256 indexed taskId);
    event RewardDistributed(uint256 indexed taskId, uint256 rewardPerAgent);

    function createTask(string memory description) external payable returns (uint256 taskId) {
        require(msg.value > 0, "Reward required");

        taskId = nextTaskId++;

        Task storage task = tasks[taskId];
        task.id = taskId;
        task.creator = msg.sender;
        task.description = description;
        task.reward = msg.value;
        task.status = TaskStatus.Created;

        emit TaskCreated(taskId, msg.sender, description, msg.value);
    }

    function joinTask(uint256 taskId) external {
        Task storage task = tasks[taskId];

        require(task.status == TaskStatus.Created || task.status == TaskStatus.InProgress, "Task not joinable");
        require(!hasJoined[taskId][msg.sender], "Already joined");

        hasJoined[taskId][msg.sender] = true;
        task.participants.push(msg.sender);
        task.status = TaskStatus.InProgress;

        emit TaskJoined(taskId, msg.sender);
    }

    function completeTask(uint256 taskId) external {
        Task storage task = tasks[taskId];

        require(msg.sender == task.creator, "Only creator can complete");
        require(task.status == TaskStatus.InProgress, "Task not in progress");
        require(task.participants.length > 0, "No participants");

        task.status = TaskStatus.Completed;

        emit TaskCompleted(taskId);
    }

    function distributeReward(uint256 taskId) external {
        Task storage task = tasks[taskId];

        require(msg.sender == task.creator, "Only creator can settle");
        require(task.status == TaskStatus.Completed, "Task not completed");
        require(task.participants.length > 0, "No participants");

        uint256 rewardPerAgent = task.reward / task.participants.length;
        task.status = TaskStatus.Settled;

        for (uint256 i = 0; i < task.participants.length; i++) {
            payable(task.participants[i]).transfer(rewardPerAgent);
        }

        emit RewardDistributed(taskId, rewardPerAgent);
    }

    function getParticipants(uint256 taskId) external view returns (address[] memory) {
        return tasks[taskId].participants;
    }
}
```

## Notes

For hackathon simplicity, use native token rewards first.

If Uniswap requires ERC-20 swap flow, then add a second version with ERC-20 rewards:

```txt
TaskMarketERC20.sol
```

But do not start with ERC-20 unless necessary. Native token flow is easier for demo.

---

# 10. Agent Design

## Agents

### Memory-read step (applies to ALL agents)

Before any `should_join` or `should_approve` decision, the agent:

1. reads its past memories from 0G Storage Log (filtered by agent_id),
2. includes a summary of past decisions and outcomes in the LLM prompt,
3. emits a `memory_read` event to the UI showing what it loaded,
4. references the past memory in the decision JSON's `reason` field.

This is the **0G read-back loop** — required for the bounty.

---

### Planner Agent

Responsibilities:

* receives user task,
* broadcasts task through AXL,
* evaluates replies,
* forms team,
* triggers contract task creation.

Decision rule:

```txt
1. Read past memory: which task types succeeded before?
2. If task reward > 0 and at least two agents reply with capability match, form team.
3. Use 0G Compute (qwen3.6-plus) to choose team composition when multiple options exist.
```

---

### Researcher Agent

Responsibilities:

* listens for tasks,
* replies if task requires research,
* produces a short research result,
* stores decision in memory.

Decision rule:

```txt
1. Read past memory: have I succeeded at similar tasks before?
2. If task contains "research", "analyze", "market", or "summary", join.
3. On second run, prior success increases confidence (lower risk_level).
```

---

### Critic Agent (NEW)

Responsibilities:

* listens for Researcher output,
* validates the output against the task description,
* either approves or sends revision request via AXL,
* gates settlement — Executor cannot complete the task until Critic approves.

Decision rule:

```txt
1. Read Researcher's output from AXL.
2. Read past critique memory from 0G Storage.
3. Use 0G Compute to evaluate: does the output address the task?
4. Emit APPROVE or REJECT_WITH_REASON message via AXL.
5. Save critique to 0G Storage Log.
```

This is the **self-fact-checking** capability the 0G bounty highlights.

---

### Executor Agent

Responsibilities:

* listens for tasks,
* replies if task requires execution,
* waits for Critic approval before submitting completion,
* submits completion,
* receives reward,
* swaps token using Uniswap.

Decision rule:

```txt
1. Read past memory: prior reward outcomes and swap results.
2. If reward exists and task requires execution, join.
3. After Critic approval, submit completion onchain.
4. After reward settlement, swap 30% of reward via Uniswap Trading API.
5. Save full task memory (decision + reward + swap tx) to 0G Storage.
```

---

## Agent Prompt Template

```txt
You are {agent_name}, a {role} agent in AgentFi City.

Your goal:
- Decide whether to join a task.
- Collaborate with other agents.
- Preserve useful memory.
- Avoid unsafe or unreasonable financial actions.

Current task:
{task}

Your wallet:
{wallet_address}

Your previous memory:
{memory}

Return JSON:
{
  "should_join": true/false,
  "reason": "...",
  "proposed_action": "...",
  "risk_level": "low" | "medium" | "high"
}
```

---

# 11. AXL Integration Plan

## Minimum AXL flow

The exact implementation depends on AXL local node APIs, but the conceptual flow should be:

```txt
1. Start AXL node for Planner
2. Start AXL node for Researcher
3. Start AXL node for Executor
4. Planner sends task announcement
5. Researcher receives and replies
6. Executor receives and replies
7. Planner receives replies and confirms team
```

AXL runs as a local binary where the app talks to localhost, while AXL handles encryption, routing, and peer discovery. The ETHGlobal bounty description also says any language that can make HTTP requests can use it. 

## Message schema

```json
{
  "message_id": "msg-001",
  "from_agent": "planner-001",
  "to_agent": "broadcast",
  "type": "TASK_ANNOUNCEMENT",
  "task": {
    "id": "task-001",
    "title": "Analyze ETH market trend",
    "reward": "0.01 ETH"
  },
  "timestamp": "2026-05-01T12:00:00Z"
}
```

Reply:

```json
{
  "message_id": "msg-002",
  "from_agent": "researcher-001",
  "to_agent": "planner-001",
  "type": "JOIN_PROPOSAL",
  "task_id": "task-001",
  "capability": "research",
  "reason": "I can summarize recent market conditions.",
  "timestamp": "2026-05-01T12:00:05Z"
}
```

Team confirmation:

```json
{
  "message_id": "msg-003",
  "from_agent": "planner-001",
  "to_agent": "researcher-001",
  "type": "TEAM_CONFIRMED",
  "task_id": "task-001",
  "participants": ["researcher-001", "executor-001"],
  "timestamp": "2026-05-01T12:00:10Z"
}
```

## Critical bounty requirement

Do not fake this only inside FastAPI.
At least two agent processes must exchange messages through AXL.

---

# 12. 0G Integration Plan

## Required 0G features

### 0G Storage (required, both KV and Log)

Use **0G Storage KV** for:

* live agent state (current status, current task, reputation score),
* "session" data that needs fast read-write during demo runs.

Use **0G Storage Log** for:

* task memory entries (one append per task),
* agent decision history,
* Critic critiques and approvals,
* final task results.

The bounty rewards using **both** storage modes. KV for real-time, Log for history.

### 0G Compute (required — promoted from optional)

At least one decision must use a live model on 0G Compute:

* Resolve the model at runtime: `await broker.inference.listService()` returns the current providers and models. Pick one and pass it through to `getServiceMetadata`. Do not hard-code model names — the 0G catalog changes.
* The Critic agent's validation call is the natural fit (it's already a reasoning step).
* Show the request payload, model name, and response in the UI.
* If 0G Compute integration blocks the demo, fall back to OpenAI for non-Critic agents but keep Critic on 0G Compute as the bounty-touching path.

0G docs describe Storage SDK support for uploading, downloading, key-value storage, browser support, and encryption/decryption. ([0G Documentation][3])

## Memory write example

After task completion:

```json
{
  "memory_type": "task_result",
  "agent_id": "researcher-001",
  "task_id": "task-001",
  "input": "Analyze ETH market trend",
  "output": "ETH sentiment appears cautiously optimistic...",
  "decision_reason": "Joined because research capability matched task requirement.",
  "timestamp": "2026-05-01T12:10:00Z"
}
```

## Memory read example

Before joining a task:

```txt
Researcher Agent reads previous memory:
- past success rate,
- preferred task type,
- previous reward result.
```

Then makes decision:

```txt
I will join this task because similar research tasks were completed successfully before.
```

## 0G Compute usage (required)

Critic agent validation call:

```txt
Critic asks 0G Compute (live model from broker.inference.listService()):
"Given task description '{task}' and Researcher output '{output}',
 does the output substantively address the task?
 Return JSON: {approved: bool, reason: string, confidence: 0-1}"
```

Show the request and response in the UI's MemoryPanel. The model name in the response payload is the bounty-visible proof.

Secondary 0G Compute call (nice-to-have): Planner uses 0G Compute to pick team composition when multiple agents claim the same capability.

---

# 13. Uniswap Integration Plan

## Required Uniswap features

* **API**: Uniswap **Trading API** at `https://trade-api.gateway.uniswap.org/v1`
* **Endpoints used**: `POST /quote` for routing + price, `POST /swap` for transaction building
* **Chain**: Base Sepolia (primary), Sepolia (backup)
* **Flow**:
  1. Agent calls `/quote` with `tokenIn`, `tokenOut`, `amount`
  2. Agent calls `/swap` to get transaction calldata
  3. Agent signs and broadcasts via its own wallet
  4. UI displays quote payload + tx hash + Etherscan/Basescan link

The Uniswap API docs describe API endpoints that abstract away smart contract complexity and use routing logic / intent-based swapping systems. ([Uniswap Developers][4])

The swapping API provides quote and transaction-building services with validation checks. ([Uniswap Developers][5])

## Swap flow

```txt
1. Executor Agent receives reward
2. Executor decides to swap 30% of reward
3. Backend requests Uniswap quote
4. Agent wallet signs / executes transaction
5. Frontend displays quote and tx hash
```

## Important

The Uniswap bounty requires `FEEDBACK.md` in the root of the repository. 

Create this file early:

```md
# Uniswap API Feedback

## What worked well

## What was confusing

## Bugs encountered

## Documentation gaps

## Feature requests

## Final notes
```

---

# 14. Frontend UI Plan

## Page layout

```txt
┌──────────────────────────────────────────────┐
│ AgentFi City                                 │
│ Onchain Autonomous Agent Economy             │
│ [Start Demo] [Reset Demo]                    │
├──────────────────────────────────────────────┤
│ Agent Cards                                  │
│ Planner | Researcher | Executor              │
├──────────────────────────────────────────────┤
│ Task Lifecycle Timeline                      │
│ Created → Broadcasted → Team Formed → ...    │
├──────────────────────────────────────────────┤
│ Live Agent Communication Logs                │
├──────────────────────────────────────────────┤
│ Onchain Transactions                         │
│ Contract tx | Reward tx | Swap tx            │
├──────────────────────────────────────────────┤
│ 0G Memory                                    │
│ Latest memory object / storage key           │
└──────────────────────────────────────────────┘
```

## Required components

### AgentCard

Displays:

* name,
* role,
* wallet,
* status,
* last action.

### TaskTimeline

Stages:

```txt
Created
Broadcasted via AXL
Team Formed
Onchain Task Created
Executing
Completed
Reward Distributed
Swap Completed
Memory Saved
```

### EventLog

Displays:

```txt
[Planner] Broadcasting task via AXL
[Researcher] Received task announcement
[Researcher] Sent join proposal
[Executor] Sent join proposal
[Contract] Task created: 0x...
[Contract] Reward distributed: 0x...
[Uniswap] Quote received
[Uniswap] Swap executed: 0x...
[0G] Memory saved: key...
```

### TransactionPanel

Displays:

* contract address,
* task tx hash,
* reward distribution tx hash,
* swap tx hash.

### MemoryPanel

Displays:

* memory JSON,
* 0G storage key / link,
* agent decision reason.

---

# 15. Backend API Plan

## Endpoints

### Health

```txt
GET /health
```

Returns:

```json
{
  "status": "ok"
}
```

---

### Start demo

```txt
POST /demo/start
```

Triggers full demo flow.

Returns:

```json
{
  "demo_id": "demo-001",
  "status": "started"
}
```

---

### Reset demo

```txt
POST /demo/reset
```

Clears local demo state.

---

### Get state

```txt
GET /demo/state
```

Returns current agents, task, logs, tx hashes.

---

### Event stream

```txt
GET /events/stream
```

Use SSE or WebSocket.

Frontend subscribes to live logs.

---

# 16. Demo Orchestration Flow

## Controlled demo sequence

Backend should run the following sequence:

```python
async def run_demo():
    emit("task_created", "User created task with reward")

    task = create_local_task()

    emit("axl_message", "Planner broadcasting task via AXL")
    await planner.broadcast_task(task)

    emit("axl_message", "Researcher received task and replied")
    researcher_reply = await researcher.wait_and_reply(task)

    emit("axl_message", "Executor received task and replied")
    executor_reply = await executor.wait_and_reply(task)

    emit("agent_decision", "Planner formed team")
    team = [researcher, executor]

    emit("contract_tx", "Creating task onchain")
    task_tx = await contract.create_task(task)

    emit("contract_tx", "Agents joining task")
    join_txs = await contract.join_task(task, team)

    emit("agent_decision", "Researcher executing task")
    research_output = await researcher.produce_output(task)

    emit("agent_decision", "Critic validating Researcher output via 0G Compute")
    critique = await critic.validate_via_og_compute(task, research_output)
    if not critique["approved"]:
        emit("agent_decision", f"Critic rejected: {critique['reason']}")
        # In demo, Researcher revises once
        research_output = await researcher.revise(task, critique)
        critique = await critic.validate_via_og_compute(task, research_output)

    emit("agent_decision", "Critic approved — Executor finalizing")
    result = await executor.finalize(task, research_output)

    emit("contract_tx", "Completing task")
    complete_tx = await contract.complete_task(task)

    emit("contract_tx", "Distributing reward")
    reward_tx = await contract.distribute_reward(task)

    emit("uniswap_quote", "Executor requesting Uniswap quote")
    quote = await uniswap.get_quote(...)

    emit("uniswap_swap", "Executor executing swap")
    swap_tx = await uniswap.execute_swap(...)

    emit("memory_write", "Saving agent memory to 0G Storage")
    memory_key = await og_storage.save_memory(...)

    emit("done", "Demo completed")
```

## Why controlled flow

This avoids demo failure while still showing real integrations.

---

# 17. Environment Variables

Create `.env.example`:

```env
# Backend
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000

# Wallets
PLANNER_PRIVATE_KEY=
RESEARCHER_PRIVATE_KEY=
EXECUTOR_PRIVATE_KEY=
TASK_CREATOR_PRIVATE_KEY=

# Chain
RPC_URL=
CHAIN_ID=
TASK_MARKET_CONTRACT_ADDRESS=

# Uniswap
UNISWAP_API_KEY=
UNISWAP_API_BASE_URL=

# 0G
OG_STORAGE_RPC=
OG_STORAGE_PRIVATE_KEY=
OG_COMPUTE_API_KEY=

# AXL
AXL_PLANNER_URL=http://localhost:7001
AXL_RESEARCHER_URL=http://localhost:7002
AXL_EXECUTOR_URL=http://localhost:7003

# LLM
OPENAI_API_KEY=
```

---

# 18. Development Phases

## Phase 1 — Skeleton UI and Backend

Goal:

Create a working frontend and backend with fake logs.

Tasks:

* Create Next.js app.
* Create FastAPI backend.
* Create `/demo/start`.
* Create frontend dashboard.
* Stream fake demo events.

Expected result:

Click button → UI shows full fake lifecycle.

This is important because the demo story must work before infra integration.

---

## Phase 2 — Smart Contract

Goal:

Add real blockchain task lifecycle.

Tasks:

* Implement `TaskMarket.sol`.
* Add tests.
* Deploy to testnet.
* Add contract service in backend.
* Show tx hashes in frontend.

Expected result:

Click demo → real task creation tx appears.

---

## Phase 3 — AXL Agent Communication

Goal:

Make agents communicate through AXL.

Tasks:

* Install / run AXL node.
* Create planner node.
* Create researcher node.
* Create executor node.
* Implement task broadcast.
* Implement join proposal.
* Send messages across separate processes.
* Capture messages in backend logs.

Expected result:

Frontend shows real AXL messages.

This is critical for Gensyn.

---

## Phase 4 — Uniswap API

Goal:

Add token swap behavior.

Tasks:

* Add Uniswap API key.
* Implement quote request.
* Implement swap transaction generation.
* Execute swap using agent wallet if testnet supported.
* Otherwise display quote and prepared transaction.
* Add `FEEDBACK.md`.

Expected result:

Frontend shows quote and swap tx/prepared tx.

This is critical for Uniswap.

---

## Phase 5 — 0G Storage

Goal:

Persist agent memory.

Tasks:

* Integrate 0G Storage SDK.
* Save memory JSON.
* Read memory before next task.
* Display memory key/link in frontend.

Expected result:

Frontend shows memory saved to 0G.

This is critical for 0G.

---

## Phase 6 — Polish

Goal:

Make the project presentable.

Tasks:

* Improve README.
* Add architecture diagram.
* Add demo script.
* Add setup instructions.
* Add troubleshooting.
* Record video under 3 minutes.
* Add bounty mapping.

---

# 19. What to Build First

Build in this exact order:

```txt
1. Frontend fake demo
2. Backend event stream
3. Smart contract
4. AXL communication
5. Uniswap quote / swap
6. 0G Storage
7. README / FEEDBACK / demo video
```

Reason:

The visual demo must always work.
If AXL or Uniswap takes longer than expected, the UI still gives structure and lets you plug integrations one by one.

---

# 20. Demo Script

## Demo title

**AgentFi City: Autonomous Agents That Coordinate, Earn, and Trade Onchain**

## 3-minute demo structure

### 0:00–0:20 — Problem

“AI agents are becoming more capable, but most of them still cannot coordinate, transact, or build economic relationships without centralized infrastructure.”

### 0:20–0:40 — Solution

“AgentFi City turns agents into onchain economic actors. Each agent has a role, wallet, memory, and peer-to-peer communication ability.”

### 0:40–1:20 — Agent coordination

Show:

* Planner creates task.
* Planner broadcasts via AXL.
* Researcher and Executor reply.
* Team forms.

Say:

“Here, the agents are not communicating through a centralized backend queue. They coordinate peer-to-peer through AXL.”

### 1:20–1:50 — Onchain settlement

Show:

* task contract,
* join task,
* complete task,
* reward distribution tx.

Say:

“The collaboration is settled onchain through our TaskMarket contract.”

### 1:50–2:20 — Financial action

Show:

* Uniswap quote,
* swap execution/prepared transaction.

Say:

“After receiving rewards, the Executor Agent uses the Uniswap API to convert part of its reward, showing real agentic finance.”

### 2:20–2:45 — Persistent memory

Show:

* memory JSON,
* 0G Storage key.

Say:

“The agent stores its decision and task history into 0G Storage, allowing future decisions to be based on persistent memory.”

### 2:45–3:00 — Vision

Say:

“This is a step toward open agent economies, where agents can discover work, coordinate, earn, trade, and evolve onchain.”

---

# 21. README Requirements

The root `README.md` should include:

```md
# AgentFi City

## What it does

## Why it matters

## Target bounties

## Architecture

## Demo flow

## Tech stack

## How we use 0G

## How we use AXL

## How we use Uniswap

## Smart contract addresses

## Setup instructions

## Running locally

## Demo video

## Team

## Contact
```

The 0G bounty asks submissions to include project name, short description, contract deployment addresses, public GitHub repo, demo video/live demo, protocol features used, team contact info, and at least one working example agent. 

---

# 22. FEEDBACK.md for Uniswap

Create `FEEDBACK.md`:

```md
# Uniswap API Feedback

## Summary

We integrated the Uniswap API to allow an autonomous agent to request a quote and execute or prepare a token swap after receiving task rewards.

## What worked well

- ...

## What was confusing

- ...

## Bugs encountered

- ...

## Documentation gaps

- ...

## Feature requests

- ...

## Final notes

- ...
```

This is mandatory for the Uniswap bounty. 

---

# 23. Bounty Mapping Document

Create `docs/bounty-mapping.md`:

```md
# Bounty Mapping

## 0G Autonomous Agents

AgentFi City uses 0G Storage to persist agent memory and task history.

Relevant features:
- multi-agent collaboration
- persistent memory
- long-running task lifecycle
- optional 0G Compute reasoning

## Gensyn AXL

AgentFi City uses AXL for peer-to-peer communication between agents.

Relevant features:
- Planner broadcasts tasks
- Researcher and Executor respond through AXL
- agents run as separate processes

## Uniswap

AgentFi City uses the Uniswap API for agentic financial execution.

Relevant features:
- quote request
- token swap
- post-reward asset management
```

---

# 24. Risk Management

## Risk 1 — AXL integration takes too long

Fallback:

* Still run separate agents.
* Use AXL for one simple message exchange only.
* Keep rest of flow controlled by backend.

Minimum acceptable proof:

```txt
Planner sends message through AXL.
Researcher receives and replies through AXL.
Frontend displays this message exchange.
```

---

## Risk 2 — Uniswap swap execution is difficult

Fallback:

* Get real Uniswap quote.
* Generate swap transaction payload.
* Display prepared transaction.
* If execution works, show tx hash.

Minimum acceptable proof:

```txt
Agent requests quote from Uniswap API.
Quote is displayed.
Agent decision references the quote.
```

But stronger demo should execute a transaction if possible.

---

## Risk 3 — 0G Compute too hard

Fallback:

* Use 0G Storage only.
* Store memory JSON.
* Read memory in second demo run.

Minimum acceptable proof:

```txt
Memory is written to 0G Storage.
Memory key/link is displayed.
```

---

## Risk 4 — Smart contract token reward too complex

Fallback:

* Use native token rewards.
* Use separate funded wallet for Uniswap swap.

Ideal flow:

```txt
Reward distributed → same agent swaps.
```

Fallback flow:

```txt
Reward distributed → agent wallet already has swap token → agent swaps.
```

---

## Risk 5 — Demo instability

Fallback:

* Add “simulation mode” toggle.
* Simulation mode uses fake logs but keeps UI working.
* Real mode attempts integrations.

Do not rely only on real-time autonomy during the pitch.

---

# 25. Success Criteria

## Minimum success

The project is successful if:

* frontend shows full task lifecycle,
* smart contract is deployed,
* at least one real task transaction happens,
* two agents communicate through AXL,
* Uniswap API quote is shown,
* 0G Storage memory is saved,
* README and FEEDBACK.md exist.

## Strong success

The project is strong if:

* three agents communicate through AXL,
* reward is distributed onchain,
* agent executes real token swap,
* memory is saved and read back from 0G,
* demo video clearly maps to all three bounties.

## Excellent success

The project is excellent if:

* agents make simple autonomous decisions,
* agent memory affects future behavior,
* frontend is polished,
* architecture diagram is clear,
* all submission requirements are complete,
* contract addresses and tx hashes are included.

---

# 26. Instructions for Codex / Claude Code

Use the following implementation priorities:

```txt
Priority 1:
Create the repo structure, frontend dashboard, backend API, and fake demo event stream.

Priority 2:
Implement TaskMarket.sol and contract service.

Priority 3:
Implement agent classes and separate process execution.

Priority 4:
Integrate AXL for message passing.

Priority 5:
Integrate Uniswap quote and swap flow.

Priority 6:
Integrate 0G Storage memory write/read.

Priority 7:
Polish README, FEEDBACK.md, architecture docs, and demo script.
```

Do not overbuild.
Do not create a complex marketplace.
Do not spend too much time on autonomous reasoning.
The demo must be reliable, understandable, and visibly connected to the bounties.

---

# 27. Final MVP Definition

The final MVP should be this:

> A user clicks “Start Demo.”
> Planner Agent broadcasts a paid task through AXL.
> Researcher and Executor Agents respond through AXL.
> The team is formed.
> A task is created and settled through a smart contract.
> Executor Agent receives reward and performs a Uniswap swap.
> The agent stores its memory into 0G Storage.
> The frontend displays every step with logs, transaction hashes, and memory records.

That is the version Codex should build first.

[1]: https://docs.gensyn.ai/tech/agent-exchange-layer?utm_source=chatgpt.com "Agent eXchange Layer (AXL) | Tech"
[2]: https://developers.uniswap.org/?utm_source=chatgpt.com "Docs | Uniswap Developers"
[3]: https://docs.0g.ai/developer-hub/building-on-0g/storage/sdk?utm_source=chatgpt.com "Storage SDK | 0G Documentation"
[4]: https://api-docs.uniswap.org/introduction?utm_source=chatgpt.com "Introduction"
[5]: https://developers.uniswap.org/docs/trading/swapping-api/integration-guide?utm_source=chatgpt.com "Swapping API Integration Guide"
