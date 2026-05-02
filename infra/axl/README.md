# AXL — Gensyn Agent eXchange Layer

This dir holds the locally-built AXL binary + node configs for the 4 agent
processes. AXL is a peer-to-peer node binary; each agent process talks to its
own localhost AXL instance, and AXL handles encryption + routing across the
Yggdrasil mesh.

## One-time install

AXL ships from source only — no pre-built releases. Requires **Go 1.25.5+**.

```bash
# 1. Install Go (macOS via brew)
brew install go
go version  # must report 1.25.5 or later

# 2. Clone + build AXL into this directory
git clone https://github.com/gensyn-ai/axl.git axl-src
cd axl-src
make build
cp ./node ../axl-node           # the built binary
cd .. && rm -rf axl-src         # cleanup source

# 3. Generate per-agent identity keys (one ed25519 key per agent)
mkdir -p keys configs
for agent in planner researcher critic executor; do
  openssl genpkey -algorithm ed25519 -out "keys/${agent}.pem"
done
```

## Per-agent node configs

Each agent runs its own AXL node. Verified port model (different from what
the README first suggested):

- `tcp_port` — gVisor app-data tunneling port; **must be the SAME** on every
  node (the dialer uses the local config to address remote peers). Default 7000.
- `api_port` — local HTTP admin API; **must be unique** per node on one machine.
- `Listen` — Yggdrasil mesh peering (TLS); one node needs to listen, others put
  the same URL in `Peers` to bootstrap.
- `PrivateKeyPath` — optional. Omit for ephemeral keys (fine for the demo).

Hub-and-spoke topology for our 4 agents (planner is the bootstrap):

| Agent | api_port | role |
|---|---|---|
| planner | 9100 | listens at `tls://127.0.0.1:9001` |
| researcher | 9101 | peers to `tls://127.0.0.1:9001` |
| critic | 9102 | peers to `tls://127.0.0.1:9001` |
| executor | 9103 | peers to `tls://127.0.0.1:9001` |

**configs/planner.json**
```json
{"Listen":["tls://127.0.0.1:9001"],"Peers":[],"tcp_port":7000,"api_port":9100}
```

**configs/researcher.json** (and critic/executor with their api_port)
```json
{"Peers":["tls://127.0.0.1:9001"],"tcp_port":7000,"api_port":9101}
```

The Python `axl_service.AXLClient` talks to the `api_port`.

## Running the 4 nodes

```bash
# Terminal 1
./axl-node -config configs/planner.json

# Terminal 2
./axl-node -config configs/researcher.json

# (etc. for critic, executor)
```

Each node prints its public key on startup — that's the peer ID used by
`/send`. You can also fetch it via `curl localhost:9100/topology | jq .our_public_key`.

Each node prints its **peer ID** on startup. Collect all 4 peer IDs and
add them to the agent process env vars (see `backend/agents/README.md`).

## Smoke test

After all 4 nodes are up:

```bash
python scripts/axl_smoke.py
```

Sends a test message planner → researcher and prints the round-trip result.
If this works, the orchestrator can be flipped to real AXL mode.

## What's gitignored

- `axl-node` binary — rebuild per machine
- `keys/*.pem` — never commit private keys
- `configs/*.json` — per-machine ports
