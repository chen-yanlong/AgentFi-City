"use client";

import { DemoEvent } from "@/lib/types";

export default function TransactionPanel({ events }: { events: DemoEvent[] }) {
  const txEvents = events.filter(
    (e) =>
      e.type === "contract_tx" ||
      e.type === "uniswap_swap" ||
      e.type === "uniswap_quote"
  );

  const txHashes = txEvents
    .map((e) => e.metadata?.tx_hash as string | undefined)
    .filter(Boolean);

  return (
    <div className="rounded-lg border border-card-border bg-card p-4">
      <h2 className="text-sm font-semibold mb-3">Onchain Transactions</h2>
      {txHashes.length === 0 && txEvents.length === 0 ? (
        <p className="text-xs text-muted">No transactions yet.</p>
      ) : (
        <div className="space-y-2">
          {txEvents.map((event) => (
            <div key={event.id} className="text-xs">
              <div className="flex items-center gap-2">
                <span className="text-accent-green font-medium">
                  {event.source}
                </span>
                <span className="text-muted">{event.message}</span>
              </div>
              {(() => {
                const txHash = event.metadata?.tx_hash as string | undefined;
                return txHash ? (
                  <div className="font-mono text-zinc-500 mt-0.5 truncate">
                    tx: {txHash}
                  </div>
                ) : null;
              })()}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
