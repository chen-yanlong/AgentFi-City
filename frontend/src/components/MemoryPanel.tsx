"use client";

import { DemoEvent } from "@/lib/types";

export default function MemoryPanel({ events }: { events: DemoEvent[] }) {
  const memoryEvents = events.filter((e) => e.type === "memory_write");
  const lastMemory = memoryEvents[memoryEvents.length - 1];

  const storageKey = lastMemory?.metadata?.storage_key as string | undefined;
  const memoryObj = lastMemory?.metadata?.memory as
    | Record<string, unknown>
    | undefined;

  return (
    <div className="rounded-lg border border-card-border bg-card p-4">
      <h2 className="text-sm font-semibold mb-3">0G Storage Memory</h2>
      {!lastMemory ? (
        <p className="text-xs text-muted">No memory saved yet.</p>
      ) : (
        <div className="space-y-2">
          {storageKey && (
            <div className="text-xs">
              <span className="text-muted">Key: </span>
              <span className="font-mono text-accent-amber">{storageKey}</span>
            </div>
          )}
          {memoryObj && (
            <pre className="text-[11px] font-mono bg-zinc-900 rounded p-3 overflow-x-auto text-zinc-300 leading-relaxed">
              {JSON.stringify(memoryObj, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
