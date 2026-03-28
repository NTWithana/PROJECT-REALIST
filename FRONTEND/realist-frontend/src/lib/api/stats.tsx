export async function fetchGlobalStats() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge/stats`);

  if (!res.ok) return null;
  return res.json();
}
