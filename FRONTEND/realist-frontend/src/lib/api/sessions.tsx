import { apiFetch } from "./client";

export async function fetchUserSessions() {
  const res = await apiFetch("/api/sessions/my");
  return res.json();
}
