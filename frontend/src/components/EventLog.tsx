"use client";

import { useEffect, useRef } from "react";
import { DemoEvent, EventType } from "@/lib/types";

const EVENT_COLORS: Record<EventType, string> = {
  task_created: "text-accent-amber",
  axl_message: "text-accent-blue",
  agent_decision: "text-accent-purple",
  critic_review: "text-amber-300",
  contract_tx: "text-accent-green",
  uniswap_quote: "text-accent-cyan",
  uniswap_swap: "text-accent-cyan",
  memory_read: "text-amber-300",
  memory_write: "text-amber-300",
  error: "text-accent-red",
  done: "text-accent-green",
};

const EVENT_PREFIX: Record<EventType, string> = {
  task_created: "TASK",
  axl_message: "AXL",
  agent_decision: "DECISION",
  critic_review: "REVIEW",
  contract_tx: "CONTRACT",
  uniswap_quote: "UNISWAP",
  uniswap_swap: "UNISWAP",
  memory_read: "0G",
  memory_write: "0G",
  error: "ERROR",
  done: "DONE",
};

export default function EventLog({ events }: { events: DemoEvent[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events.length]);

  return (
    <div className="rounded-lg border border-card-border bg-card flex flex-col">
      <h2 className="text-sm font-semibold p-4 pb-2">Live Agent Communication</h2>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 pt-0 max-h-[300px]">
        {events.length === 0 ? (
          <p className="text-xs text-muted py-4 text-center">
            No events yet. Start the demo to see agent activity.
          </p>
        ) : (
          <div className="space-y-1 font-mono text-xs">
            {events.map((event) => (
              <div key={event.id} className="flex gap-2 leading-relaxed">
                <span className="text-zinc-600 shrink-0">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
                <span
                  className={`shrink-0 font-semibold ${EVENT_COLORS[event.type]}`}
                >
                  [{EVENT_PREFIX[event.type]}]
                </span>
                <span className="text-zinc-400 shrink-0">[{event.source}]</span>
                <span className="text-foreground">{event.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
