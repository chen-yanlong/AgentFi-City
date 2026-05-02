# Uniswap Trading API — Builder Feedback

## Summary

We integrated the Uniswap Trading API into AgentFi City — a 4-agent onchain
swarm where the Executor agent swaps 30% of its task reward (WETH → USDC on
Base Sepolia) immediately after settlement. The integration lives in
[`backend/services/uniswap_service.py`](backend/services/uniswap_service.py)
and uses two endpoints (`/quote` + `/swap`) plus Permit2 EIP-712 signing in
Python via `eth_account`.

Below is honest feedback after building against the docs and the live API.

---

## What worked well

- **Two-endpoint design covers the canonical path.** `/quote` then `/swap` is
  the entire mental model. No separate routing/quoter/calldata lookup —
  refreshing compared to having to wire up the Quoter contract directly.
- **Returned `TransactionRequest` is directly broadcastable.** All fields
  (`to`, `data`, `value`, `chainId`, `gasLimit`, `maxFeePerGas`,
  `maxPriorityFeePerGas`) come back ready to sign and ship — no manual
  router-encoding, no reading function selectors, no calldata padding.
- **Permit2 model is genuinely gasless.** EIP-712 signing means the user
  doesn't pay for an approval tx — clear UX win and good for hackathon
  agents that have minimal gas.
- **Base Sepolia is supported via API even though the web UI doesn't show
  it.** This was a pleasant surprise — most Uniswap surfaces only expose
  Sepolia + Unichain Sepolia, but the API quietly supports Base Sepolia +
  Arbitrum Sepolia too. Saved us from having to fall back to mainnet for
  the demo.
- **OpenAPI spec at `/v1/api.json`.** Easy to grep through and confirm field
  names without round-tripping the docs site.
- **`type: "EXACT_INPUT"` vs `EXACT_OUTPUT` is well-named.** Self-explanatory
  — no surprises about which side is locked.
- **Slippage is a single percent number.** `slippageTolerance: 0.5` is much
  saner than basis points or 1e6 fractions.
- **Error responses include enough detail to debug.** When a quote fails,
  the response body usually tells you why (insufficient liquidity, unknown
  token, etc.) without needing to dig.
- **Routing field tells you whether you're getting Classic or UniswapX.**
  Useful for surfacing in the UI ("agent got a UniswapX intent route").
- **Rate limit failures (HTTP 429) are explicit** — easy to detect and
  back off vs. silent throttling.
- **API-key model is simple.** One header (`x-api-key`), one dashboard,
  done. No OAuth dance or per-request signing on the auth itself.

---

## What was confusing

- **"Trading API" vs "Swapping API" vs "Routing API" — three names for
  overlapping things.** Docs at `developers.uniswap.org` use all three
  inconsistently. Took ~20 minutes to confirm we wanted the Trading API
  for our use case (agent that swaps post-settlement).
- **Permit2 "both fields or neither" rule isn't loud enough.** The docs
  mention you must pass `signature` + `permitData` together or omit both,
  but it's easy to send `signature` without `permitData` if the quote
  didn't return one and your code path doesn't branch correctly. A 400
  with `"Provide both signature and permitData, or neither"` would be
  more helpful than the current generic 400.
- **Multiple amount-encoding conventions in one response.** Some fields
  are decimal strings (`"amount": "1500000000000000"`), some are
  prefixed-hex (`"value": "0x0"`), some are raw numbers. Had to write
  `int(x, 0) if isinstance(x, str) else int(x)` defensively.
- **Permit2 `domain.chainId` vs `quote.tokenInChainId` — same value,
  different field names.** Easy to mix up which chainId to send back to
  `/swap`.
- **Quote response shape differs by routing type** (Classic vs UniswapX).
  We had to add a discriminator check before building the swap request.
  A union type or `routing_version` field at the top level would help.
- **No clear "does this token need approval" hint until you see whether
  `permitData` is null.** A boolean at the top level (`permit_required`)
  would save a check.
- **Domain/types/values structure for EIP-712 signing took time.**
  Mapping Uniswap's `permitData.domain/types/values` to Python's
  `eth_account.encode_typed_data(domain_data, message_types,
  message_data)` requires careful field renaming. A worked Python
  example would have saved us 30 min.
- **Supported-chains page is separate from the integration guide.**
  `/contracts/v3/reference/deployments/...` lists chains but not
  whether Trading API works there. We had to find a Trading-API-
  specific page later.
- **API key tier limits aren't documented upfront.** We don't know how
  many requests/min the free tier gets. Hit one 429 during dev and had
  to guess.
- **No "test network only" mode flag.** When you set `tokenInChainId:
  84532`, you're already signaling testnet, but a separate
  `dryRun: true` (no broadcast, just simulation) would be ideal for
  hackathon prototyping.

---

## Bugs encountered

- **Quote occasionally returns successfully with `quote.amount = "0"`**
  for low-liquidity testnet pairs. Caller has no graceful path other
  than detecting the zero amount manually. Suggest returning a 422
  with `"insufficient liquidity"` instead of a 200 with a zero quote.
- **`chainId` in the swap response is sometimes a stringified integer
  ("84532") and sometimes a number (84532)** depending on routing.
  Forces defensive type-coercion on the client side.
- **`gasLimit` field intermittently missing** for very small swaps —
  fell back to a hard-coded 500000 default in our client. Would prefer
  the server always return one (even if conservative).
- **Hitting `/quote` with `tokenInChainId != tokenOutChainId` returns
  500** (cross-chain not supported) instead of 400. Misleading.

---

## Documentation gaps

- **No Python integration example anywhere.** All examples are TypeScript
  / ethers.js. Fine for the web3 majority, but agent backends are
  increasingly Python (LangChain, LlamaIndex, FastAPI). A worked
  Python+web3.py+eth_account example would 10x onboarding for that
  audience. Specifically: how to translate `permitData` → `encode_typed_data`
  is the part that's not obvious.
- **Permit2 details are scattered across protocol docs and Trading API
  docs.** A single "Permit2 for API users" page would help — linking to
  Uniswap's protocol-level Permit2 spec assumes the reader cares about
  the underlying contract, which API users often don't.
- **No error-response taxonomy.** What does each 4xx code mean?
  Currently you guess from the body string. A table of error codes
  with `code → meaning → recommended client action` would be great.
- **Rate limit numbers absent from docs.** Even ballpark figures
  ("~60 req/min for free tier, 600/min for paid") would let us design
  retry/backoff intelligently.
- **No documented testnet mocking strategy.** For hackathon teams without
  funded wallets at noon on day 1, a sandbox endpoint that returns
  realistic shapes without requiring tokens would unblock local dev.
- **Per-chain feature matrix unclear.** Does UniswapX work on Base
  Sepolia? Which chains support `EXACT_OUTPUT`? Hard to know without
  trying.
- **No webhooks mentioned.** Implied that you poll the chain yourself
  for tx confirmation. A webhook-on-confirmation would simplify backend
  design.
- **No batch-quote endpoint documented.** For agents that compare
  multiple pairs ("would WETH→USDC or WETH→DAI net me more?"), having
  to make N parallel quote requests is wasteful.

---

## Feature requests

- **Python SDK** (or even an unofficial reference) — current docs leave
  Python builders to write their own httpx wrappers + EIP-712 helpers.
- **Sandbox / dry-run mode** — `dryRun: true` returns the same response
  shape but doesn't actually execute on-chain. Critical for hackathon
  weekend when funded testnet wallets are scarce.
- **Batch quote endpoint** — `POST /quotes` taking an array of pairs.
- **Webhook-on-tx-confirmation** — register a callback URL, get pinged
  when the swap tx confirms (with status + receipt).
- **`permit_required: bool` at the top level of the quote response** —
  saves a `permitData != null` check.
- **Discriminator field for routing type** at the top level (e.g.
  `routing_version: "classic" | "uniswapx-v1"`) so clients can branch
  cleanly without inferring shape.
- **Per-API-key dashboard with usage graphs** — currently you only see
  "you got 429'd" after the fact.
- **OpenAPI spec discoverability** — the spec at `/v1/api.json` is
  great but isn't linked from the integration guide. Add a "Generate
  client SDK from this spec" callout.
- **Native cross-chain swap intent** — for agents that earn on chain A
  and want to swap on chain B, having the API handle bridging would
  remove a major hackathon-week-eating problem.
- **Per-token risk metadata** — return a flag for honeypots /
  rug-suspect tokens, especially on testnets where anyone can deploy.

---

## Final notes

- **Overall ergonomics are good for the canonical path.** Quote → sign
  permit → swap works exactly as you'd hope. The complexity surfaces
  only at the edges (Permit2 in non-JS langs, error taxonomy,
  rate limits).
- **Hackathon-friendly: yes, *if* you have an API key + funded testnet
  wallet ahead of time.** First-time setup is the bottleneck, not the
  API itself. A sandbox mode would change this completely.
- **Most surprising friction:** Permit2 EIP-712 signing in Python —
  not Uniswap's fault per se (the standard is what it is), but the
  Trading API docs assume a JS audience that has ethers.js helpers
  available. Our wrapper at
  [`uniswap_service.py:_sign_permit`](backend/services/uniswap_service.py)
  shows what it took in Python.
- **What we wish existed most:** a `dryRun` mode. Hackathon teams
  spend disproportionate time hunting faucets and approving Permit2 —
  any of that we could skip during dev would let us iterate faster on
  the actual product.
- **Would we use the Trading API again?** Yes. The TX-ready response is
  worth the integration cost on its own — much better than wiring up
  the Universal Router calldata ourselves.

— *AgentFi City team, ETHGlobal Open Agents 2026*
