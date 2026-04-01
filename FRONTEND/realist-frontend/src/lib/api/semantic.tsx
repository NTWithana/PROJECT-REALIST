import { apiFetch } from "./client";

export async function semanticSearch(
  query: string,
  domain?: string,
  tags?: string[]
) {
  const params = new URLSearchParams({ query });

  if (domain) params.append("domain", domain);
  if (tags?.length) tags.forEach(t => params.append("tags", t));

  const res = await apiFetch(
    `/api/knowledge/semantic-similar?${params.toString()}`
  );

  return res.json();
}
