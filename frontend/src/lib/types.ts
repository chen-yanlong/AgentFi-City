export type AgentRole = "planner" | "researcher" | "executor";

export type AgentStatus =
  | "idle"
  | "listening"
  | "negotiating"
  | "working"
  | "paid"
  | "swapped";

export interface Agent {
  id: string;
  name: string;
  role: AgentRole;
  wallet_address: string;
  status: AgentStatus;
  memory_key?: string;
}

export type TaskStatus =
  | "created"
  | "broadcasted"
  | "team_forming"
  | "team_formed"
  | "executing"
  | "completed"
  | "settled"
  | "swapped"
  | "memory_saved";

export interface Task {
  id: string;
  onchain_task_id?: number;
  title: string;
  description: string;
  reward_token: string;
  reward_amount: string;
  status: TaskStatus;
  participants: string[];
  tx_hashes: string[];
}

export type EventType =
  | "task_created"
  | "axl_message"
  | "agent_decision"
  | "contract_tx"
  | "uniswap_quote"
  | "uniswap_swap"
  | "memory_write"
  | "error"
  | "done";

export interface DemoEvent {
  id: string;
  timestamp: string;
  source: string;
  type: EventType;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface DemoState {
  demo_id: string | null;
  agents: Agent[];
  task: Task | null;
  events: DemoEvent[];
  is_running: boolean;
}
