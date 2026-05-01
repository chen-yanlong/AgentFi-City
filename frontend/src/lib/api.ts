const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function startDemo(): Promise<{ demo_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/demo/start`, { method: "POST" });
  return res.json();
}

export async function resetDemo(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/demo/reset`, { method: "POST" });
  return res.json();
}

export async function getDemoState() {
  const res = await fetch(`${API_BASE}/demo/state`);
  return res.json();
}

export function createEventSource(): EventSource {
  return new EventSource(`${API_BASE}/events/stream`);
}
