export async function fetchUserSessions() {
  const token = localStorage.getItem("token");

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sessions`, {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (!res.ok) return [];

  return res.json();
}
