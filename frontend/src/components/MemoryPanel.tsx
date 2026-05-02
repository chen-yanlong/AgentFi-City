"use client";

import { DemoEvent } from "@/lib/types";

export default function MemoryPanel({ events }: { events: DemoEvent[] }) {
  const memoryEvents = events.filter((e) => e.type === "memory_write");
  const lastMemory = memoryEvents[memoryEvents.length - 1];

  const storageKey = lastMemory?.metadata?.storage_key as string | undefined;
  const explorerUrl = lastMemory?.metadata?.explorer_url as string | undefined;
  const realUpload = lastMemory?.metadata?.real_upload as boolean | undefined;
  const memoryObj = lastMemory?.metadata?.memory as
    | Record<string, unknown>
    | undefined;

  return (
    <div className="rounded-lg border border-card-border bg-card p-4">
      <h2 className="text-sm font-semibold mb-3">
        0G Storage Memory
        {realUpload && (
          <span className="ml-2 text-[10px] text-accent-green font-normal">
            • live
          </span>
        )}
      </h2>
      {!lastMemory ? (
        <p className="text-xs text-muted">No memory saved yet.</p>
      ) : (
        <div className="space-y-2">
          {storageKey && (
            <div className="text-xs">
              <span className="text-muted">Root hash: </span>
              {explorerUrl ? (
                <a
                  href={explorerUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-accent-amber hover:underline truncate inline-block max-w-full align-bottom"
                >
                  {storageKey}
                </a>
              ) : (
                <span className="font-mono text-accent-amber">{storageKey}</span>
              )}
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
