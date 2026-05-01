/**
 * 0G Compute Network sidecar
 *
 * Wraps @0gfoundation/0g-compute-ts-sdk as a small HTTP service so the
 * Python backend can call inference without re-implementing the broker.
 *
 * Required env:
 *   OG_PRIVATE_KEY    — wallet that holds funded ledger account on 0G testnet
 *
 * Optional env:
 *   OG_RPC_URL        — defaults to 0G Galileo testnet RPC
 *   OG_PROVIDER       — pin a specific provider address; otherwise picks first acknowledged
 *   PORT              — defaults to 7100
 */

import express, { type Request, type Response } from "express";
import { Wallet, JsonRpcProvider } from "ethers";
import { createZGComputeNetworkBroker } from "@0gfoundation/0g-compute-ts-sdk";

const PORT = Number(process.env.PORT || 7100);
const RPC_URL = process.env.OG_RPC_URL || "https://evmrpc-testnet.0g.ai";
const PRIVATE_KEY = process.env.OG_PRIVATE_KEY || "";
const PINNED_PROVIDER = process.env.OG_PROVIDER || "";

interface BrokerState {
  ready: boolean;
  walletAddress?: string;
  providerAddress?: string;
  model?: string;
  endpoint?: string;
  startupError?: string;
  broker?: Awaited<ReturnType<typeof createZGComputeNetworkBroker>>;
}

const state: BrokerState = { ready: false };

async function initBroker() {
  if (!PRIVATE_KEY) {
    state.startupError =
      "OG_PRIVATE_KEY is not set — sidecar will run but /infer will return 503";
    console.warn(`[og-compute-sidecar] ${state.startupError}`);
    return;
  }

  try {
    const provider = new JsonRpcProvider(RPC_URL);
    const wallet = new Wallet(PRIVATE_KEY, provider);
    state.walletAddress = wallet.address;

    const broker = await createZGComputeNetworkBroker(wallet);
    state.broker = broker;

    const services = await broker.inference.listService();
    if (services.length === 0) {
      state.startupError = "No inference providers available on 0G Compute";
      console.warn(`[og-compute-sidecar] ${state.startupError}`);
      return;
    }

    const chosen =
      (PINNED_PROVIDER &&
        services.find(
          (s) => s.provider.toLowerCase() === PINNED_PROVIDER.toLowerCase()
        )) ||
      services[0];
    state.providerAddress = chosen.provider;

    const metadata = await broker.inference.getServiceMetadata(chosen.provider);
    state.endpoint = metadata.endpoint;
    state.model = metadata.model;

    state.ready = true;
    console.log(
      `[og-compute-sidecar] ready: provider=${state.providerAddress} model=${state.model} endpoint=${state.endpoint}`
    );
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    state.startupError = `Broker init failed: ${msg}`;
    console.error(`[og-compute-sidecar] ${state.startupError}`);
  }
}

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req: Request, res: Response) => {
  res.json({
    ready: state.ready,
    wallet: state.walletAddress,
    provider: state.providerAddress,
    model: state.model,
    endpoint: state.endpoint,
    startup_error: state.startupError,
  });
});

interface InferBody {
  messages: { role: "user" | "system" | "assistant"; content: string }[];
  max_tokens?: number;
  response_format?: { type: "json_object" | "text" };
}

app.post("/infer", async (req: Request, res: Response) => {
  if (!state.ready || !state.broker) {
    return res
      .status(503)
      .json({ error: "sidecar not ready", detail: state.startupError });
  }

  const body = req.body as InferBody;
  if (!body.messages || !Array.isArray(body.messages)) {
    return res.status(400).json({ error: "messages array required" });
  }

  // Bill against the concatenated user content (per SDK example)
  const userContent = body.messages
    .filter((m) => m.role === "user")
    .map((m) => m.content)
    .join("\n");

  try {
    const headers = await state.broker.inference.getRequestHeaders(
      state.providerAddress!,
      userContent
    );

    const upstream = await fetch(`${state.endpoint}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(headers as unknown as Record<string, string>),
      },
      body: JSON.stringify({
        messages: body.messages,
        model: state.model,
        max_tokens: body.max_tokens,
        response_format: body.response_format,
      }),
    });

    if (!upstream.ok) {
      const text = await upstream.text();
      return res.status(502).json({
        error: "upstream provider error",
        status: upstream.status,
        body: text.slice(0, 1000),
      });
    }

    const raw = await upstream.json();
    const content = raw?.choices?.[0]?.message?.content ?? "";

    // Best-effort fee accounting (cache miss is fine for short-lived requests)
    const chatID = upstream.headers.get("ZG-Res-Key") || raw?.id || "";
    if (chatID) {
      state.broker.inference
        .processResponse(state.providerAddress!, chatID, JSON.stringify(raw?.usage ?? ""))
        .catch((e) => console.warn("[og-compute-sidecar] processResponse:", e));
    }

    res.json({
      model: state.model,
      provider: state.providerAddress,
      content,
      raw,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    res.status(500).json({ error: "inference failed", detail: msg });
  }
});

app.listen(PORT, async () => {
  console.log(`[og-compute-sidecar] listening on :${PORT}`);
  await initBroker();
});
