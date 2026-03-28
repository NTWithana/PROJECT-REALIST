export async function semanticSearch(query: string, domain?: string, tags?: string[]) {
  const params = new URLSearchParams({ query });

  if (domain) params.append("domain", domain);
  if (tags && tags.length > 0) {
    tags.forEach((t) => params.append("tags", t));
  }

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge/semantic-similar?${params.toString()}`);

  if (!res.ok) return [];
  return res.json();
}
