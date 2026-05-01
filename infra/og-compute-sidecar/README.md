# 0G Compute Sidecar

Small Node.js HTTP wrapper around `@0gfoundation/0g-compute-ts-sdk` so the
Python backend can call 0G Compute Network inference without re-implementing
the broker.

## Architecture

```
backend/llm_service.py  ──HTTP──>  this sidecar (:7100)  ──>  0G Compute broker  ──>  provider /chat/completions
```

The Python `llm_service` falls back to OpenAI then to a hardcoded verdict if
the sidecar is unavailable, so the demo flow never breaks.

## Endpoints

- `GET /health` — broker status, wallet, provider, model, endpoint
- `POST /infer` — body `{ messages, max_tokens?, response_format? }` returns `{ model, provider, content, raw }`

## Setup (one-time)

1. Get a 0G Galileo testnet wallet and **fund it** at <https://faucet.0g.ai>.
2. Use the 0G Compute CLI to create a ledger account and deposit funds — the
   broker can't make inference calls without it. See the SDK CLI:
   ```bash
   npx 0g-compute-cli ledger create --rpc https://evmrpc-testnet.0g.ai --key $OG_PRIVATE_KEY
   npx 0g-compute-cli ledger deposit --amount 0.1 --key $OG_PRIVATE_KEY
   ```
3. Install deps:
   ```bash
   npm install
   ```

## Run

```bash
OG_PRIVATE_KEY=0x...  npm start
```

Optional env:

- `OG_RPC_URL` — defaults to `https://evmrpc-testnet.0g.ai`
- `OG_PROVIDER` — pin a specific provider address (otherwise picks the first acknowledged)
- `PORT` — defaults to `7100`

## Verify

```bash
curl localhost:7100/health
# expect ready=true with provider/model populated

curl -X POST localhost:7100/infer \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"reply with just OK"}]}'
```

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `/health` shows `ready=false` with `OG_PRIVATE_KEY is not set` | env not exported | `export OG_PRIVATE_KEY=0x...` |
| `/health` shows `No inference providers available` | network temporarily empty or chain ID wrong | retry, or pin via `OG_PROVIDER` |
| `/infer` returns 502 | upstream provider error (often: ledger account not funded) | top up via CLI deposit |
| `/infer` returns 503 | broker init failed at startup | see startup_error in `/health` |
