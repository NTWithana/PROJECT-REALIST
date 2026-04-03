import json
from datetime import datetime

from models import gpt5_nano
from chat_signals import write_chat_signal

MODEL_TIMEOUT_FAST = 8.0

MEGA_PROMPT = """You are a lightweight AI controller inside a cost-optimized multi-model system.

You act as a deterministic orchestrator.

Your job:
- understand input
- classify intent
- estimate complexity
- decide if deeper reasoning is required
- extract memory signals
- detect inconsistencies
- create a minimal plan
- generate optimized structured instructions
- optionally generate a short response

Be concise, structured, and consistent.

---

### TASKS (DO ALL IN ONE PASS)

1. Intent:
["chat", "question", "task", "problem", "planning", "other"]

2. Complexity:
["low", "medium", "high"]

3. Confidence (0–1)

4. use_reasoner = true IF:
- multi-step reasoning
- ambiguity
- debugging / optimization / system design
- confidence < 0.55

5. Memory signal (or null):
{
  "topic": "...",
  "user_goal": "...",
  "importance": 0–1
}

6. Inconsistency detection:
true/false

7. Task plan:
1–3 short steps max

8. Instructions:
{
  "goal": "...",
  "constraints": "...",
  "expected_output": "...",
  "notes": "..."
}

9. Draft response:
ONLY if complexity = low or medium

---

### RULES

- Output STRICT JSON only
- No extra text
- Be deterministic
- Keep tokens LOW
- Do NOT hallucinate
- Do NOT over-escalate
- If unsure → lower confidence

---

### INPUT

USER_INPUT:
{user_input}

SESSION_CONTEXT:
{short_context_or_summary}

---

Return JSON only."""

def now():
    return datetime.utcnow()

def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except:
        return {}

async def chat_pipeline(
    message: str,
    *,
    mode: str = "chat",
    domain: str = "general",
    tags=None,
    session_id=None,
    user_id=None
) -> dict:

    msg = (message or "")[:1400]

    controller_prompt = MEGA_PROMPT.format(
        user_input=msg,
        short_context_or_summary=""
    )

    raw = await gpt5_nano(controller_prompt, timeout=MODEL_TIMEOUT_FAST)
    ctrl = safe_json_loads(raw)

    response = ctrl.get("draft_response") or "I'm thinking about this."

    # ---------- MEMORY SIGNAL ----------
    signal = ctrl.get("memory_signal")
    if signal:
        await write_chat_signal({
            "pattern": signal.get("topic"),
            "importance": signal.get("importance"),
            "message": msg,
            "response": response,
            "sessionId": session_id,
            "userId": user_id,
            "createdAt": now().isoformat() + "Z"
        })

    return {
        "response": response,
        "confidence": ctrl.get("confidence", 0.6),
        "intent": ctrl.get("intent", "chat"),
        "mode": mode,
        "model_used": "gpt5_nano",
        "used_global_rag": False,
        "used_chat_signals": bool(signal),
        "cache_hit": False
    }