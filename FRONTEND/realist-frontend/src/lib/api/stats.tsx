import { apiFetch } from "./client";

export async function fetchGlobalStats() {
  const res = await apiFetch("/api/knowledge/stats");
  return res.json();
}
