"use client";

import { TaskStatus } from "@/lib/types";

const STAGES: { key: TaskStatus; label: string }[] = [
  { key: "created", label: "Created" },
  { key: "broadcasted", label: "Broadcasted" },
  { key: "team_forming", label: "Team Forming" },
  { key: "team_formed", label: "Team Formed" },
  { key: "executing", label: "Executing" },
  { key: "completed", label: "Completed" },
  { key: "settled", label: "Settled" },
  { key: "swapped", label: "Swapped" },
  { key: "memory_saved", label: "Memory Saved" },
];

function getStageIndex(status: TaskStatus | null): number {
  if (!status) return -1;
  return STAGES.findIndex((s) => s.key === status);
}

export default function TaskTimeline({
  status,
}: {
  status: TaskStatus | null;
}) {
  const currentIndex = getStageIndex(status);

  return (
    <div className="rounded-lg border border-card-border bg-card p-4">
      <h2 className="text-sm font-semibold mb-3">Task Lifecycle</h2>
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {STAGES.map((stage, i) => {
          const isComplete = i <= currentIndex;
          const isCurrent = i === currentIndex;

          return (
            <div key={stage.key} className="flex items-center">
              <div className="flex flex-col items-center gap-1 min-w-[72px]">
                <div
                  className={`w-3 h-3 rounded-full border-2 transition-colors ${
                    isCurrent
                      ? "border-accent-green bg-accent-green animate-status-pulse"
                      : isComplete
                        ? "border-accent-green bg-accent-green"
                        : "border-zinc-600 bg-transparent"
                  }`}
                />
                <span
                  className={`text-[10px] text-center leading-tight ${isCurrent ? "text-foreground font-medium" : isComplete ? "text-muted" : "text-zinc-600"}`}
                >
                  {stage.label}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <div
                  className={`w-4 h-px mt-[-14px] ${isComplete ? "bg-accent-green" : "bg-zinc-700"}`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
