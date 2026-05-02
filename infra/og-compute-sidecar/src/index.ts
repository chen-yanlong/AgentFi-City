/**
 * 0G sidecar
 *
 * Wraps the 0G TypeScript SDKs (compute + storage) as a small HTTP service so
 * the Python backend can use them without re-implementing the brokers.
 *
 * Required env:
 *   OG_PRIVATE_KEY    — wallet that holds funded ledger account on 0G testnet
 *
 * Optional env:
 *   OG_RPC_URL                — defaults to 0G Galileo testnet RPC
 *   OG_PROVIDER               — pin a specific compute provider address
 *   OG_STORAGE_INDEXER_URL    — defaults to Turbo testnet indexer
 *   PORT                      — defaults to 7100
 */

import express, { type Request, type Response } from "express";
import { Wallet, JsonRpcProvider } from "ethers";
import { createZGComputeNetworkBroker } from "@0gfoundation/0g-compute-ts-sdk";
import { Indexer, MemData } from "@0gfoundation/0g-storage-ts-sdk";

const PORT = Number(process.env.PORT || 7100);
const RPC_URL = process.env.OG_RPC_URL || "https://evmrpc-testnet.0g.ai";
const PRIVATE_KEY = process.env.OG_PRIVATE_KEY || "";
const PINNED_PROVIDER = process.env.OG_PROVIDER || "";
const STORAGE_INDEXER_URL =
  process.env.OG_STORAGE_INDEXER_URL ||
  "https://indexer-storage-testnet-turbo.0g.ai";

interface ComputeState {
  ready: boolean;
  providerAddress?: string;
  model?: string;
  endpoint?: string;
  startupError?: string;
  broker?: Awaited<ReturnType<typeof createZGComputeNetworkBroker>>;
}

interface StorageState {
  ready: boolean;
  indexerUrl: string;
  startupError?: string;
  indexer?: Indexer;
}

const state = {
  walletAddress: undefined as string | undefined,
  wallet: undefined as Wallet | undefined,
  compute: { ready: false } as ComputeState,
  storage: { ready: false, indexerUrl: STORAGE_INDEXER_URL } as StorageState,
};

async function initWallet() {
  if (!PRIVATE_KEY) {
    const msg =
      "OG_PRIVATE_KEY is not set — sidecar will run but inference and storage endpoints will return 503";
    state.compute.startupError = msg;
    state.storage.startupError = msg;
    console.warn(`[og-sidecar] ${msg}`);
    return;
  }
  const provider = new JsonRpcProvider(RPC_URL);
  state.wallet = new Wallet(PRIVATE_KEY, provider);
  state.walletAddress = state.wallet.address;
}

async function initCompute() {
  if (!state.wallet) return;
  try {
    const broker = await createZGComputeNetworkBroker(state.wallet);
    state.compute.broker = broker;

    const services = await broker.inference.listService();
    if (services.length === 0) {
      state.compute.startupError = "No inference providers available";
      console.warn(`[og-sidecar] compute: ${state.compute.startupError}`);
      return;
    }

    const chosen =
      (PINNED_PROVIDER &&
        services.find(
          (s) => s.provider.toLowerCase() === PINNED_PROVIDER.toLowerCase()
        )) ||
      services[0];

    state.compute.providerAddress = chosen.provider;
    const metadata = await broker.inference.getServiceMetadata(chosen.provider);
    state.compute.endpoint = metadata.endpoint;
    state.compute.model = metadata.model;
    state.compute.ready = true;
    console.log(
      `[og-sidecar] compute ready: provider=${state.compute.providerAddress} model=${state.compute.model}`
    );
  } catch (e) {
    state.compute.startupError = `Compute init failed: ${e instanceof Error ? e.message : String(e)}`;
    console.error(`[og-sidecar] ${state.compute.startupError}`);
  }
}

async function initStorage() {
  if (!state.wallet) return;
  try {
    state.storage.indexer = new Indexer(STORAGE_INDEXER_URL);
    state.storage.ready = true;
    console.log(`[og-sidecar] storage ready: indexer=${STORAGE_INDEXER_URL}`);
  } catch (e) {
    state.storage.startupError = `Storage init failed: ${e instanceof Error ? e.message : String(e)}`;
    console.error(`[og-sidecar] ${state.storage.startupError}`);
  }
}

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req: Request, res: Response) => {
  res.json({
    wallet: state.walletAddress,
    compute: {
      ready: state.compute.ready,
      provider: state.compute.providerAddress,
      model: state.compute.model,
      endpoint: state.compute.endpoint,
      startup_error: state.compute.startupError,
    },
    storage: {
      ready: state.storage.ready,
      indexer_url: state.storage.indexerUrl,
      startup_error: state.storage.startupError,
    },
  });
});

interface InferBody {
  messages: { role: "user" | "system" | "assistant"; content: string }[];
  max_tokens?: number;
  response_format?: { type: "json_object" | "text" };
}

app.post("/infer", async (req: Request, res: Response) => {
  if (!state.compute.ready || !state.compute.broker) {
    return res
      .status(503)
      .json({ error: "compute not ready", detail: state.compute.startupError });
  }

  const body = req.body as InferBody;
  if (!body.messages || !Array.isArray(body.messages)) {
    return res.status(400).json({ error: "messages array required" });
  }

  const userContent = body.messages
    .filter((m) => m.role === "user")
    .map((m) => m.content)
    .join("\n");

  try {
    const headers = await state.compute.broker.inference.getRequestHeaders(
      state.compute.providerAddress!,
      userContent
    );

    const upstream = await fetch(`${state.compute.endpoint}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(headers as unknown as Record<string, string>),
      },
      body: JSON.stringify({
        messages: body.messages,
        model: state.compute.model,
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

    const chatID = upstream.headers.get("ZG-Res-Key") || raw?.id || "";
    if (chatID) {
      state.compute.broker.inference
        .processResponse(
          state.compute.providerAddress!,
          chatID,
          JSON.stringify(raw?.usage ?? "")
        )
        .catch((e) => console.warn("[og-sidecar] processResponse:", e));
    }

    res.json({
      model: state.compute.model,
      provider: state.compute.providerAddress,
      content,
      raw,
    });
  } catch (e) {
    res.status(500).json({
      error: "inference failed",
      detail: e instanceof Error ? e.message : String(e),
    });
  }
});

interface UploadBody {
  content: string;
}

app.post("/storage/upload", async (req: Request, res: Response) => {
  if (!state.storage.ready || !state.storage.indexer || !state.wallet) {
    return res
      .status(503)
      .json({ error: "storage not ready", detail: state.storage.startupError });
  }

  const body = req.body as UploadBody;
  if (typeof body.content !== "string") {
    return res.status(400).json({ error: "content (string) required" });
  }

  try {
    const bytes = new TextEncoder().encode(body.content);
    const file = new MemData(bytes);
    const [result, err] = await state.storage.indexer.upload(
      file,
      RPC_URL,
      state.wallet
    );
    if (err) {
      return res.status(500).json({ error: "upload failed", detail: err.message });
    }

    // Result is either single or batched — normalize
    const rootHash =
      "rootHash" in result ? result.rootHash : result.rootHashes[0];
    const txHash = "txHash" in result ? result.txHash : result.txHashes[0];
    res.json({ rootHash, txHash, indexer_url: STORAGE_INDEXER_URL });
  } catch (e) {
    res.status(500).json({
      error: "upload exception",
      detail: e instanceof Error ? e.message : String(e),
    });
  }
});

app.get("/storage/download/:rootHash", async (req: Request, res: Response) => {
  if (!state.storage.ready || !state.storage.indexer) {
    return res
      .status(503)
      .json({ error: "storage not ready", detail: state.storage.startupError });
  }

  try {
    const [blob, err] = await state.storage.indexer.downloadToBlob(
      req.params.rootHash
    );
    if (err) {
      return res
        .status(500)
        .json({ error: "download failed", detail: err.message });
    }
    const content = await blob.text();
    res.json({ rootHash: req.params.rootHash, content });
  } catch (e) {
    res.status(500).json({
      error: "download exception",
      detail: e instanceof Error ? e.message : String(e),
    });
  }
});

app.listen(PORT, async () => {
  console.log(`[og-sidecar] listening on :${PORT}`);
  await initWallet();
  await Promise.all([initCompute(), initStorage()]);
});
