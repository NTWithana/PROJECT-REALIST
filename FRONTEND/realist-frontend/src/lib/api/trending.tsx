import { apiFetch } from "./client";

export async function fetchTrending(limit = 20) {
  const res = await apiFetch(
    `/api/knowledge/trending?limit=${limit}`
  );
  return res.json();
}
