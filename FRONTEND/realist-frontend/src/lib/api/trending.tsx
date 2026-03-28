export async function fetchTrending(limit = 20) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge/trending?limit=${limit}`);

  if (!res.ok) return [];
  return res.json();
}
