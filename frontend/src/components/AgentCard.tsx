"use client";

import { Agent, AgentStatus } from "@/lib/types";

const STATUS_CONFIG: Record<
  AgentStatus,
  { label: string; color: string; pulse: boolean }
> = {
  idle: { label: "Idle", color: "bg-zinc-500", pulse: false },
  listening: { label: "Listening", color: "bg-accent-blue", pulse: true },
  negotiating: {
    label: "Negotiating",
    color: "bg-accent-amber",
    pulse: true,
  },
  working: { label: "Working", color: "bg-accent-purple", pulse: true },
  reviewing: { label: "Reviewing", color: "bg-amber-300", pulse: true },
  paid: { label: "Paid", color: "bg-accent-green", pulse: false },
  swapped: { label: "Swapped", color: "bg-accent-cyan", pulse: false },
};

const ROLE_ICON: Record<string, string> = {
  planner: "P",
  researcher: "R",
  critic: "C",
  executor: "E",
};

const ROLE_COLOR: Record<string, string> = {
  planner: "border-accent-blue",
  researcher: "border-accent-purple",
  critic: "border-amber-300",
  executor: "border-accent-green",
};

export default function AgentCard({ agent }: { agent: Agent }) {
  const status = STATUS_CONFIG[agent.status];

  return (
    <div className="rounded-lg border border-card-border bg-card p-4 flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div
          className={`w-10 h-10 rounded-full border-2 ${ROLE_COLOR[agent.role]} flex items-center justify-center text-sm font-bold font-mono`}
        >
          {ROLE_ICON[agent.role]}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm">{agent.name}</h3>
          <p className="text-xs text-muted capitalize">{agent.role}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${status.color} ${status.pulse ? "animate-status-pulse" : ""}`}
          />
          <span className="text-xs text-muted">{status.label}</span>
        </div>
      </div>

      <div className="text-xs font-mono text-muted truncate">
        {agent.wallet_address}
      </div>
    </div>
  );
}
