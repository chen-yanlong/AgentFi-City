"use client";

import { useState } from "react";
import { Agent, DemoEvent, TaskStatus } from "@/lib/types";
import AgentCard from "@/components/AgentCard";
import TaskTimeline from "@/components/TaskTimeline";
import EventLog from "@/components/EventLog";
import TransactionPanel from "@/components/TransactionPanel";
import MemoryPanel from "@/components/MemoryPanel";

const INITIAL_AGENTS: Agent[] = [
  {
    id: "planner-001",
    name: "Planner",
    role: "planner",
    wallet_address: "0x0000000000000000000000000000000000000001",
    status: "idle",
  },
  {
    id: "researcher-001",
    name: "Researcher",
    role: "researcher",
    wallet_address: "0x0000000000000000000000000000000000000002",
    status: "idle",
  },
  {
    id: "executor-001",
    name: "Executor",
    role: "executor",
    wallet_address: "0x0000000000000000000000000000000000000003",
    status: "idle",
  },
];

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [events, setEvents] = useState<DemoEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const handleStart = async () => {
    // Will connect to backend SSE in commit 4
    setIsRunning(true);
  };

  const handleReset = () => {
    setAgents(INITIAL_AGENTS);
    setTaskStatus(null);
    setEvents([]);
    setIsRunning(false);
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-card-border px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">AgentFi City</h1>
            <p className="text-xs text-muted mt-0.5">
              Onchain Autonomous Agent Economy
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleStart}
              disabled={isRunning}
              className="px-4 py-2 text-sm font-medium rounded-md bg-accent-green text-black hover:bg-accent-green/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning ? "Running..." : "Start Demo"}
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium rounded-md border border-card-border text-muted hover:text-foreground hover:border-zinc-500 transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 px-6 py-6">
        <div className="max-w-6xl mx-auto space-y-4">
          {/* Agent cards */}
          <section>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
          </section>

          {/* Task timeline */}
          <TaskTimeline status={taskStatus} />

          {/* Two-column layout: Event Log + Side panels */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <EventLog events={events} />
            </div>
            <div className="space-y-4">
              <TransactionPanel events={events} />
              <MemoryPanel events={events} />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-card-border px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-muted">
          <span>AgentFi City — ETHGlobal Open Agents 2025</span>
          <span>0G + AXL + Uniswap</span>
        </div>
      </footer>
    </div>
  );
}
