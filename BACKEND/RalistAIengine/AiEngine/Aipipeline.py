import json
import hashlib
from datetime import datetime

from Models import ProblemReq, Finalresult
from redis_cache import redis_get_json, redis_set_json
from rag import retrieve_rag
from models import gpt5_nano, deepseek_reasoner
from session_graph import update_graph
from code_graph import update_code_graph

CONF_DEFAULT = 0.6
MODEL_TIMEOUT_FAST = 8.0
MODEL_TIMEOUT_DEEP = 18.0

MEGA_PROMPT = """You are a lightweight AI controller.

Return STRICT JSON:
{
 "intent": "",
 "complexity": "",
 "confidence": 0.0,
 "use_reasoner": true/false,
 "inconsistency_detected": true/false,
 "instructions_for_worker": {},
 "draft_response": ""
}

INPUT:
{user_input}
"""

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
        "inconsistency_detected": False,
        "instructions_for_worker": {},
        "draft_response": None
    }

def fallback_core(solution, confidence, sources):
    return {
        "solution": solution,
        "critique": "May contain gaps.",
        "improvements": "Add validation.",
        "reasoning": "",
        "confidence": max(0.4, confidence),
        "sources": sources,
        "uncertainty": ["Limited context"],
        "next_step": "Validate before applying"
    }

# ---------- MAIN ----------
async def AIpipeline(problem: ProblemReq) -> Finalresult:
    cleaned = (problem.description or "")[:2400]

    cache_key = f"solver:final:{problem.sessionId}:{stable_hash(cleaned)}"
    cached = await redis_get_json(cache_key)
    if cached:
        return Finalresult(**cached)

    # ---------- CONTROLLER ----------
    ctrl_raw = await gpt5_nano(
        MEGA_PROMPT.format(user_input=cleaned),
        timeout=MODEL_TIMEOUT_FAST
    )
    ctrl = safe_json_loads(ctrl_raw) or fallback_ctrl()

    # ---------- RAG ----------
    use_rag = ctrl.get("complexity") in ("medium", "high")
    context, retrieved_ids, rag_cache_hit = await retrieve_rag(problem, use_rag)

    complexity = ctrl.get("complexity", "medium")
    confidence = float(ctrl.get("confidence", CONF_DEFAULT))

    # ---------- MODE ----------
    if complexity == "low" and confidence > 0.7:
        mode = "fast"
    elif complexity == "medium":
        mode = "hybrid"
    else:
        mode = "deep"

    if ctrl.get("inconsistency_detected"):
        mode = "deep"

    # ---------- BASE ----------
    core = fallback_core(
        ctrl.get("draft_response") or cleaned,
        confidence,
        retrieved_ids
    )

    deep_cache_key = f"deep:{stable_hash(cleaned + context)}"
    deep_cache = await redis_get_json(deep_cache_key)

    # ---------- HYBRID ----------
    if mode == "hybrid":
        if deep_cache:
            core = deep_cache
            deep_cache_hit = True
        else:
            deep = await deepseek_reasoner(cleaned, timeout=MODEL_TIMEOUT_DEEP)
            parsed = safe_json_loads(deep)
            if parsed and "solution" in parsed:
                core = parsed
            await redis_set_json(deep_cache_key, core, 86400)
            deep_cache_hit = False

    # ---------- DEEP ----------
    elif mode == "deep":
        if deep_cache:
            core = deep_cache
            deep_cache_hit = True
        else:
            deep1 = safe_json_loads(
                await deepseek_reasoner(cleaned, timeout=MODEL_TIMEOUT_DEEP)
            ) or core

            try:
                deep2 = safe_json_loads(
                    await deepseek_reasoner(
                        f"Improve solution:\n{json.dumps(deep1)}",
                        timeout=MODEL_TIMEOUT_DEEP
                    )
                )
                core = deep2 if deep2 and "solution" in deep2 else deep1
            except:
                core = deep1

            await redis_set_json(deep_cache_key, core, 86400)
            deep_cache_hit = False
    else:
        deep_cache_hit = False

    # ---------- REFLECTION ----------
    try:
        reflect = await gpt5_nano(
            f"Improve + add uncertainty + next step JSON:\n{json.dumps(core)}",
            timeout=MODEL_TIMEOUT_FAST
        )
        parsed = safe_json_loads(reflect)
        if parsed and "solution" in parsed:
            core = parsed
    except:
        pass

    # ---------- SESSION GRAPH ----------
    try:
        signal = safe_json_loads(
            await gpt5_nano(
                f"Extract entities/dependencies JSON:\n{cleaned}",
                timeout=MODEL_TIMEOUT_FAST
            )
        )
        if signal and problem.sessionId:
            signal["timestamp"] = now().isoformat()
            await update_graph(problem.sessionId, signal)
    except:
        pass

    # ---------- CODE GRAPH (AST-lite) ----------
    is_code = any(k in cleaned.lower() for k in [
        "class", "function", "api", "repo", "interface", "c#", "ts", "js", "python"
    ])

    if is_code:
        try:
            code_data = safe_json_loads(
                await gpt5_nano(
                    f"Extract code structure JSON (file, symbols, depends_on):\n{cleaned}",
                    timeout=MODEL_TIMEOUT_FAST
                )
            )
            if code_data and problem.sessionId:
                await update_code_graph(problem.sessionId, code_data)
        except:
            pass

    core["confidence"] = min(core.get("confidence", 0.7), 0.92)

    result = Finalresult(
        Status="ok",
        OptimisedSolution=core.get("solution"),
        Critique=core.get("critique"),
        Improvements=core.get("improvements"),
        Confidence=core.get("confidence"),
        Rationale=f"intent={ctrl.get('intent')} | mode={mode}",
        Iteration=2 if mode == "deep" else 1,
        Created_At=now(),
        DeepCore=core.get("reasoning", ""),
        UsedRag=use_rag,
        UsedDeep=mode in ("hybrid", "deep"),
        RagCacheHit=rag_cache_hit,
        DeepCacheHit=deep_cache_hit,
        ProblemKey=cache_key,
        RetrievedKnowledgeIds=core.get("sources", retrieved_ids)
    )

    await redis_set_json(cache_key, result.__dict__, 21600)
    return result