"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Agent, DemoEvent, TaskStatus } from "@/lib/types";
import { startDemo, resetDemo, getDemoState, createEventSource } from "@/lib/api";
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
    id: "critic-001",
    name: "Critic",
    role: "critic",
    wallet_address: "0x0000000000000000000000000000000000000003",
    status: "idle",
  },
  {
    id: "executor-001",
    name: "Executor",
    role: "executor",
    wallet_address: "0x0000000000000000000000000000000000000004",
    status: "idle",
  },
];

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [events, setEvents] = useState<DemoEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const syncState = useCallback(async () => {
    try {
      const state = await getDemoState();
      setAgents(state.agents);
      setTaskStatus(state.task?.status ?? null);
      setIsRunning(state.is_running);
    } catch {
      // Silently ignore poll failures
    }
  }, []);

  const stopListening = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const handleStart = async () => {
    setError(null);
    setEvents([]);
    setTaskStatus(null);
    setAgents(INITIAL_AGENTS);

    try {
      await startDemo();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start demo");
      return;
    }

    setIsRunning(true);

    // Connect to SSE stream
    const es = createEventSource();
    eventSourceRef.current = es;

    // Listen for all event types from the backend
    const eventTypes = [
      "task_created",
      "axl_message",
      "agent_decision",
      "critic_review",
      "contract_tx",
      "uniswap_quote",
      "uniswap_swap",
      "memory_write",
      "error",
      "done",
    ];

    for (const type of eventTypes) {
      es.addEventListener(type, (e: MessageEvent) => {
        const event: DemoEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, event]);

        if (type === "done") {
          setIsRunning(false);
          stopListening();
          // Final state sync
          syncState();
        }
      });
    }

    es.onerror = () => {
      // SSE disconnected — sync state and stop
      syncState();
    };

    // Poll state every 2s to keep agents/task in sync
    pollRef.current = setInterval(syncState, 2000);
  };

  const handleReset = async () => {
    stopListening();
    try {
      await resetDemo();
    } catch {
      // Ignore
    }
    setAgents(INITIAL_AGENTS);
    setTaskStatus(null);
    setEvents([]);
    setIsRunning(false);
    setError(null);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => stopListening();
  }, [stopListening]);

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
          <div className="flex items-center gap-3">
            {error && (
              <span className="text-xs text-accent-red">{error}</span>
            )}
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
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 px-6 py-6">
        <div className="max-w-6xl mx-auto space-y-4">
          {/* Agent cards */}
          <section>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
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
