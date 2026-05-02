# 0G Sidecar

Node.js HTTP wrapper around the 0G TypeScript SDKs (compute + storage) so the
Python backend can use them without re-implementing the brokers.

> Folder still named `og-compute-sidecar/` for git-history continuity, but the
> service now covers both 0G Compute and 0G Storage.

## Architecture

```
backend/llm_service.py       ──HTTP──>  /infer
backend/og_storage_service.py ──HTTP──>  /storage/upload, /storage/download
                                  │
                          this sidecar (:7100)
                                  │
                ┌─────────────────┴─────────────────┐
        0G Compute broker                    0G Storage indexer
                │                                   │
        provider /chat/completions           Galileo testnet nodes
```

The Python services fall back gracefully when the sidecar is unavailable, so
the demo flow never breaks.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | wallet, compute readiness/provider/model, storage readiness/indexer |
| POST | `/infer` | `{ messages, max_tokens?, response_format? }` → `{ model, provider, content, raw }` |
| POST | `/storage/upload` | `{ content }` → `{ rootHash, txHash, indexer_url }` |
| GET | `/storage/download/:rootHash` | → `{ rootHash, content }` |

## Setup (one-time)

1. Get a 0G Galileo testnet wallet and **fund it** at <https://faucet.0g.ai>.
2. For 0G Compute: create + deposit into a ledger account (the broker can't
   make inference calls without it):
   ```bash
   npx 0g-compute-cli ledger create --rpc https://evmrpc-testnet.0g.ai --key $OG_PRIVATE_KEY
   npx 0g-compute-cli ledger deposit --amount 0.1 --key $OG_PRIVATE_KEY
   ```
3. For 0G Storage: faucet `0G` is enough — uploads pay per-segment from the wallet.
4. Install deps:
   ```bash
   npm install
   ```

## Run

```bash
OG_PRIVATE_KEY=0x...  npm start
```

Optional env:

- `OG_RPC_URL` — defaults to `https://evmrpc-testnet.0g.ai`
- `OG_PROVIDER` — pin a specific compute provider (else picks first acknowledged)
- `OG_STORAGE_INDEXER_URL` — defaults to Turbo testnet indexer
- `PORT` — defaults to `7100`

## Verify

```bash
curl localhost:7100/health
# expect compute.ready=true and storage.ready=true with wallet populated

curl -X POST localhost:7100/infer \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"reply with just OK"}]}'

curl -X POST localhost:7100/storage/upload \
  -H 'Content-Type: application/json' \
  -d '{"content":"{\"hello\":\"0g\"}"}'
# returns { rootHash, txHash, indexer_url }

curl localhost:7100/storage/download/<rootHash>
# returns { rootHash, content: "{\"hello\":\"0g\"}" }
```

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| both compute + storage `ready=false`, error mentions `OG_PRIVATE_KEY` | env not exported | `export OG_PRIVATE_KEY=0x...` |
| compute `ready=false`, "No inference providers" | network temporarily empty | retry, or pin via `OG_PROVIDER` |
| `/infer` returns 502 | upstream provider error (often: ledger account not funded) | top up via CLI deposit |
| `/storage/upload` returns 500 with "out of funds" | wallet has no `0G` for segment fees | refill from faucet |
