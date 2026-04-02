import { apiFetch } from "@/lib/api/client";
import { useSupervisor } from "./useSupervisor";
import { useMemoryEvolution } from "./useMemoryEvolution";

export async function runSupervisor(sessionId: string) {
  const supervisor = useSupervisor.getState();
  supervisor.setLoading(true);

  // Fetch session intelligence
  const [timeline, consistency] = await Promise.all([
    apiFetch(`/api/sessions/${sessionId}/timeline`).then((r) => r.json()),
    apiFetch(`/api/sessions/${sessionId}/consistency`).then((r) => r.json()),
  ]);

  // Send to AI engine
  const ai = await apiFetch("/api/hub/assistant", {
    method: "POST",
    body: JSON.stringify({
      message: `
You are the session supervisor.

Timeline:
${JSON.stringify(timeline, null, 2)}

Consistency issues:
${JSON.stringify(consistency, null, 2)}

Return JSON:
{
  "summary": "...",
  "risks": ["..."],
  "nextActions": ["..."],
  "signals": [
    {
      "domain": "software-architecture",
      "summary": "Clear separation between OS-level context and workspace logic prevents cognitive overload.",
      "pattern": "Separate global cognition from task execution layers.",
      "confidence": 0.87
    }
  ]
}
      `,
    }),
  }).then((r) => r.json());

  const parsed = JSON.parse(ai.response);

  const memory = useMemoryEvolution.getState();

if (parsed.signals?.length) {
  memory.addSignals(
    parsed.signals.map((s: any) => ({
      ...s,
      id: crypto.randomUUID(),
      sourceSessionId: sessionId,
    }))
  );
}

  supervisor.setSupervisorData(parsed);
  supervisor.setLoading(false);
}
