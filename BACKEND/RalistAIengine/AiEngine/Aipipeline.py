import json
import hashlib
from datetime import datetime

from Models import ProblemReq, Finalresult
from redis_cache import redis_get_json, redis_set_json
from rag import retrieve_rag
from models import gpt5_nano, deepseek_reasoner

CONF_DEFAULT = 0.6
MODEL_TIMEOUT_FAST = 8.0
MODEL_TIMEOUT_DEEP = 18.0

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

5. Memory signal (or null)

6. Inconsistency detection:
true/false

7. Task plan:
1–3 steps

8. Instructions:
{
  "goal": "...",
  "constraints": "...",
  "expected_output": "...",
  "notes": "..."
}

9. Draft response if simple

---

### RULES

- STRICT JSON only
- deterministic
- no hallucination
- minimal tokens

---

### INPUT

USER_INPUT:
{user_input}

SESSION_CONTEXT:
{short_context_or_summary}

---

Return JSON only."""

# ---------- HELPERS ----------

def now():
    return datetime.utcnow()

def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except:
        return None

def fallback_ctrl():
    return {
        "intent": "problem",
        "complexity": "medium",
        "confidence": 0.5,
        "use_reasoner": True,
        "memory_signal": None,
        "inconsistency_detected": False,
        "task_plan": ["analyze", "solve"],
        "instructions_for_worker": {
            "goal": "Solve problem",
            "constraints": "Be correct",
            "expected_output": "Clear solution",
            "notes": ""
        },
        "draft_response": None
    }

def fallback_core(solution, confidence, sources):
    return {
        "solution": solution,
        "critique": "May contain logical gaps or missing validation.",
        "improvements": "Add validation and handle edge cases.",
        "reasoning": "",
        "confidence": max(0.4, confidence),
        "sources": sources
    }

# ---------- MAIN ----------

async def AIpipeline(problem: ProblemReq) -> Finalresult:
    cleaned = (problem.description or "")[:2400]

    cache_key = f"solver:final:{problem.sessionId}:{stable_hash(cleaned)}"
    cached = await redis_get_json(cache_key)
    if cached:
        return Finalresult(**cached)

    controller_prompt = MEGA_PROMPT.format(
        user_input=cleaned,
        short_context_or_summary=""
    )

    ctrl_raw = await gpt5_nano(controller_prompt, timeout=MODEL_TIMEOUT_FAST)
    ctrl = safe_json_loads(ctrl_raw) or fallback_ctrl()

    # ---------- RAG ----------
    use_rag = ctrl["complexity"] in ("medium", "high")
    context, retrieved_ids, rag_cache_hit = await retrieve_rag(problem, use_rag)

    # ---------- ROUTING ----------
    use_deep = (
        ctrl.get("use_reasoner") is True
        or ctrl.get("confidence", 0.5) < 0.5
        or ctrl.get("complexity") == "high"
    )

    deep_cache_key = f"deep:{stable_hash(cleaned + context)}"
    deep_cache = await redis_get_json(deep_cache_key)

    if use_deep:
        if deep_cache:
            core = deep_cache
            deep_cache_hit = True
        else:
            deep_prompt = f"""
You are an advanced reasoning engine.

Internally:
1. Solve
2. Critique
3. Improve

---

INSTRUCTIONS:
{json.dumps(ctrl.get("instructions_for_worker", {}))}

PROBLEM:
{cleaned}

CONTEXT:
{context}

---

OUTPUT JSON:

{{
  "solution": "...",
  "critique": "...",
  "improvements": "...",
  "reasoning": "...",
  "confidence": 0.0,
  "sources": []
}}

---

RULES:
- Self-correct internally
- No intermediate steps
- No hallucination
"""

            try:
                deep_raw = await deepseek_reasoner(deep_prompt, timeout=MODEL_TIMEOUT_DEEP)
                parsed = safe_json_loads(deep_raw)

                if parsed and "solution" in parsed:
                    core = parsed
                else:
                    core = fallback_core(
                        ctrl.get("draft_response") or cleaned,
                        ctrl.get("confidence", CONF_DEFAULT),
                        retrieved_ids
                    )

            except:
                core = fallback_core(
                    ctrl.get("draft_response") or cleaned,
                    ctrl.get("confidence", CONF_DEFAULT),
                    retrieved_ids
                )

            await redis_set_json(deep_cache_key, core, ttl_seconds=86400)
            deep_cache_hit = False
    else:
        core = fallback_core(
            ctrl.get("draft_response") or cleaned,
            ctrl.get("confidence", CONF_DEFAULT),
            retrieved_ids
        )
        deep_cache_hit = False

    # ---------- NORMALIZE ----------
    core["confidence"] = min(core.get("confidence", 0.7), 0.9)

    result = Finalresult(
        Status="ok",
        OptimisedSolution=core["solution"],
        Critique=core["critique"],
        Improvements=core["improvements"],
        Confidence=core["confidence"],
        Rationale=f"intent={ctrl['intent']} | complexity={ctrl['complexity']}",
        Iteration=1,
        Created_At=now(),
        DeepCore=core.get("reasoning", ""),
        UsedRag=use_rag,
        UsedDeep=use_deep,
        RagCacheHit=rag_cache_hit,
        DeepCacheHit=deep_cache_hit,
        ProblemKey=cache_key,
        RetrievedKnowledgeIds=core.get("sources", retrieved_ids)
    )

    await redis_set_json(cache_key, result.__dict__, ttl_seconds=21600)
    return result