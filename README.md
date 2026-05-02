# AgentFi City

> A decentralized onchain economy where autonomous AI agents coordinate
> peer-to-peer, complete tasks, earn rewards, and trade — all settled onchain.

ETHGlobal Open Agents 2026 hackathon submission targeting **0G**, **Gensyn AXL**, and **Uniswap**.

---

## What it does

Click "Start Demo" and watch a 4-agent swarm run a full economic cycle:

```
Task announced (with ETH reward)
  → Agents read past memories from 0G Storage before deciding
  → Agents negotiate via real AXL P2P messages to form a team
  → Team joins the task onchain via the TaskMarket contract
  → Researcher produces output → Critic validates via 0G Compute (LLM call)
  → Executor finalizes; contract distributes ETH reward equally
  → Executor swaps 30% of reward via the Uniswap Trading API on Base Sepolia
  → Executor saves the full task memory back to 0G Storage
  → Next run: agents make different/more confident decisions because they
    read what happened last time (memory loop closes)
```

Every step shows up live in the dashboard with real tx hashes, real model
names, and clickable explorer links.

## The swarm

| Agent | Role | Bounty hook |
|---|---|---|
| **Planner** | Broadcasts task, picks team | AXL message originator |
| **Researcher** | Produces analysis output | 0G Storage memory read-back |
| **Critic** | Validates output via LLM (gates settlement) | 0G Compute reasoning call |
| **Executor** | Submits completion, claims reward, swaps via Uniswap, persists memory | Uniswap swap, 0G Storage write |

## Architecture

```
┌────────────────────────┐
│   Frontend (Next.js)    │  ◀── SSE event stream
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│  Backend (FastAPI)       │  Demo orchestrator
└┬───────┬───────┬───────┬─┘
 │       │       │       │
 ▼       ▼       ▼       ▼
[AXL] [Contract] [Uniswap] [0G Sidecar]
4 nodes  Web3.py   Trading    Compute +
(Go)      eth_acct  API       Storage SDK
                              (TS, via HTTP)
 │       │       │       │
 ▼       ▼       ▼       ▼
P2P    TaskMarket Base    0G Galileo
mesh   contract   Sepolia testnet
```

Detailed architecture + sequence diagrams live in [docs/architecture.md](docs/architecture.md).

## Bounty alignment

### 🟣 0G — Best Autonomous Agents, Swarms & iNFT Innovations

- **4-agent swarm** matches the bounty's literal example (planner + researcher + critic + executor)
- **0G Storage** — both write (task memory, real root hash on `storagescan-galileo.0g.ai`) and read-back (agents fetch past memories before deciding)
- **0G Compute** — Critic's validation is a real inference call routed through the [og-compute-sidecar](infra/og-compute-sidecar/) (Node.js wrapper around `@0gfoundation/0g-compute-ts-sdk` since the SDK is TS-only); model name surfaces in the UI
- **0G Chain** — TaskMarket contract deployable to Galileo testnet (Hardhat config supports it)

### 🔵 Gensyn — Best Application of AXL

- **4 separate AXL node binaries** (Go) run as their own OS processes
- **Real P2P** — every `axl_message` event in the orchestrator is a real `/send` + `/recv` round-trip with matching `msg_id`. No central message broker.
- **A2A-style structured envelope**: `{msg_id, from_agent, to_agent, type, body, timestamp}`
- **9 logical exchanges per demo run**: TASK_ANNOUNCEMENT × 3, JOIN_PROPOSAL × 3, TEAM_CONFIRMED × 3, OUTPUT_FOR_REVIEW, APPROVE/REJECT
- Verified end-to-end: 22 AXL events, all `real_axl: true`, with msg_id round-trip

### 🦄 Uniswap — Best Uniswap API Integration

- **Trading API** at `https://trade-api.gateway.uniswap.org/v1` — `/quote` + `/swap`
- **Permit2 EIP-712 signing** in Python via `eth_account.encode_typed_data`
- **Real onchain execution** on Base Sepolia — agent signs the returned `TransactionRequest` and broadcasts via web3.py
- **Clickable Basescan link** in the UI for every swap tx
- **Substantive [FEEDBACK.md](FEEDBACK.md)** with what worked, friction points, doc gaps, and concrete feature requests

## Tech stack

- **Frontend**: Next.js 16 + TypeScript + Tailwind v4 (SSE-driven dashboard)
- **Backend**: FastAPI + Python 3.9 + httpx + web3.py + eth_account + openai
- **Smart contract**: Solidity 0.8.24 + Hardhat + ethers v6 + 16 passing TS tests
- **0G sidecar**: Node.js (tsx) + `@0gfoundation/0g-compute-ts-sdk` + `@0gfoundation/0g-storage-ts-sdk`
- **AXL**: Gensyn's `axl-node` binary (Go 1.25.5) — built locally, 4 instances per run

## Repository layout

```
agentfi-city/
├── frontend/                 # Next.js dashboard
├── backend/                  # FastAPI orchestrator + service modules
│   ├── main.py
│   ├── orchestrator.py       # 13-step demo lifecycle
│   ├── routes/               # /demo, /events SSE, /health
│   ├── schemas/              # Pydantic models
│   └── services/
│       ├── contract_service.py
│       ├── llm_service.py    # 0G Compute → OpenAI → fallback
│       ├── og_compute_service.py
│       ├── og_storage_service.py
│       ├── memory_index.py
│       ├── uniswap_service.py
│       └── axl_service.py
├── contracts/                # Hardhat: TaskMarket.sol + tests + deploy script
├── infra/
│   ├── og-compute-sidecar/   # Node sidecar for 0G Compute + Storage
│   └── axl/                  # AXL binary + per-agent configs
├── scripts/
│   └── axl_smoke.py          # Two-node real-AXL round-trip test
├── data/                     # memory_index.json (gitignored)
├── docs/                     # architecture, demo script, bounty mapping
├── README.md
├── FEEDBACK.md               # Required by Uniswap bounty
└── plan.md                   # Original product/dev plan
```

## Smart contract

`TaskMarket.sol` ([contracts/contracts/TaskMarket.sol](contracts/contracts/TaskMarket.sol)) — native-token rewards, equal split among participants. 16 Hardhat tests cover the happy path + revert cases.

| Network | Address | Explorer |
|---|---|---|
| Hardhat localhost | (ephemeral) | — |
| Base Sepolia | _deploy via `npm run deploy:basesepolia`_ | https://sepolia.basescan.org |
| 0G Galileo | _deploy via `npm run deploy:0g`_ | https://chainscan-galileo.0g.ai |

## Setup

Three modes depending on how much you want to wire up.

### Mode 1 — Mock (zero setup, fake hashes)

```bash
# Terminal 1: backend
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend && nvm use 20 && npm run dev
```

Open <http://localhost:3000> → click **Start Demo**.

### Mode 2 — Real local contract (real onchain tx)

Mode 1 plus a Hardhat node + deploy + flag:

```bash
# Terminal 3: hardhat node
cd contracts && nvm use 20 && npm run node

# Terminal 4: deploy (one-time)
cd contracts && nvm use 20 && npm run deploy:local

# Restart backend with USE_REAL_CONTRACT=true
USE_REAL_CONTRACT=true uvicorn backend.main:app --reload --port 8000
```

### Mode 3 — Full real (sidecar + Uniswap + AXL + 0G memory loop)

External setup (~30 min one-time):

1. **0G**: get a Galileo testnet wallet, fund at <https://faucet.0g.ai>, then:
   ```bash
   cd infra/og-compute-sidecar && npm install
   npx 0g-compute-cli ledger create --rpc https://evmrpc-testnet.0g.ai --key 0x...
   npx 0g-compute-cli ledger deposit --amount 0.1 --key 0x...
   OG_PRIVATE_KEY=0x... npm start    # Terminal 5
   ```

2. **AXL**: install Go, build the binary, run 4 nodes (see [infra/axl/README.md](infra/axl/README.md)):
   ```bash
   brew install go
   cd infra/axl && git clone https://github.com/gensyn-ai/axl.git axl-src && cd axl-src && make build && cp ./node ../axl-node
   # Terminals 6-9 — one per agent
   ./axl-node -config configs/planner.json
   ./axl-node -config configs/researcher.json
   ./axl-node -config configs/critic.json
   ./axl-node -config configs/executor.json
   ```

3. **Uniswap**: register at <https://developers.uniswap.org/dashboard> for an API key, fund Executor wallet on Base Sepolia, wrap a tiny bit of WETH, approve Permit2.

4. Set in `.env`:
   ```bash
   USE_REAL_CONTRACT=true
   USE_REAL_AXL=true
   USE_REAL_UNISWAP=true
   UNISWAP_API_KEY=...
   UNISWAP_TOKEN_IN=0x4200000000000000000000000000000000000006   # WETH on Base Sepolia
   UNISWAP_TOKEN_OUT=0x036CbD53842c5426634e7929541eC2318f3dCF7e  # USDC on Base Sepolia
   EXECUTOR_PRIVATE_KEY=0x...
   ```

5. Restart backend. Click **Start Demo**. Watch all integrations light up.

Every integration has a graceful fallback — if 0G is down, Critic uses OpenAI; if Uniswap key missing, fake quote with fake hash; etc. The visual flow always completes.


## Acknowledgments

Built on the shoulders of:

- **0G Labs** — Storage, Compute, Chain SDKs
- **Gensyn** — AXL P2P node and reference Collaborative Autoresearch Demo
- **Uniswap Foundation** — Trading API, Permit2 contract
