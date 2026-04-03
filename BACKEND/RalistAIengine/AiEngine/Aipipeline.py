# aiengine_aipipeline_fixed.py
import json
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from Models import ProblemReq, Finalresult
from redis_cache import redis_get_json, redis_set_json
from rag import retrieve_rag
from models import gpt5_nano, deepseek_reasoner
from session_graph import update_graph
from code_graph import update_code_graph

logger = logging.getLogger("aiengine")
logging.basicConfig(level=logging.INFO)

CONF_DEFAULT = 0.6
MODEL_TIMEOUT_FAST = 8.0
MODEL_TIMEOUT_DEEP = 18.0
DEEP_CACHE_TTL = 86400
FINAL_CACHE_TTL = 21600

MEGA_PROMPT = """You are a lightweight AI controller in a multi-model system.
Return STRICT JSON ONLY:
{
 "intent": "chat | question | task | problem | planning | other",
 "complexity": "low | medium | high",
 "confidence": 0.0,
 "use_reasoner": true/false,
 "inconsistency_detected": true/false,
 "instructions_for_worker": {
   "goal": "",
   "constraints": "",
   "expected_output": "",
   "notes": ""
 },
 "draft_response": ""
}
RULES:
- deterministic
- minimal tokens
- no hallucination
- use_reasoner = true if multi-step / ambiguity / confidence < 0.55
INPUT:
{user_input}
"""

def now():
    return datetime.utcnow()

def stable_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()

def safe_json_loads(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        try:
            import re
            m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass
    return None

async def safe_model_call(fn, *args, timeout: float, retries: int = 1):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            res = await fn(*args, timeout=timeout)
            if isinstance(res, str):
                return res
            return str(res)
        except Exception as e:
            last_exc = e
            logger.warning("Model call failed (attempt %d): %s", attempt + 1, e)
    logger.error("Model call failed after retries: %s", last_exc)
    return ""

def fallback_ctrl() -> Dict[str, Any]:
    return {
        "intent": "problem",
        "complexity": "medium",
        "confidence": 0.5,
        "use_reasoner": True,
        "inconsistency_detected": False,
        "instructions_for_worker": {},
        "draft_response": None
    }

def fallback_core(solution: str, confidence: float, sources: List[str]) -> Dict[str, Any]:
    return {
        "solution": solution,
        "critique": "May contain gaps.",
        "improvements": "Add validation.",
        "reasoning": "",
        "confidence": max(0.4, float(confidence or CONF_DEFAULT)),
        "sources": sources or [],
        "uncertainty": ["Limited context"],
        "next_step": "Validate before applying"
    }

# ---------- AUTO EVOLUTION ----------
async def auto_evolve(core: Dict[str, Any]) -> Dict[str, Any]:
    try:
        base_conf = float(core.get("confidence", 0.6))

        # cost control gate
        if base_conf >= 0.78 or len(core.get("solution", "")) < 50:
            return core

        prompt = f"""
Evaluate and improve this solution.

Return STRICT JSON:
{{
 "score": 0.0,
 "issues": [],
 "improved_solution": "",
 "confidence": 0.0
}}

RULES:
- score = quality (0-1)
- only improve if needed
- keep concise

INPUT:
{json.dumps(core)}
"""

        raw = await safe_model_call(
            gpt5_nano,
            prompt,
            timeout=MODEL_TIMEOUT_FAST,
            retries=0
        )

        parsed = safe_json_loads(raw)
        if not parsed:
            return core

        score = float(parsed.get("score", 1.0))

        if score < 0.7:
            core["solution"] = parsed.get("improved_solution") or core["solution"]
            core["confidence"] = max(score, 0.5)
            core["uncertainty"] = parsed.get("issues", [])

        # evaluation trace
        core["evaluation"] = {
            "score": score,
            "evaluated_at": now().isoformat()
        }

        return core

    except Exception as e:
        logger.debug("Auto-evolve skipped: %s", e)
        return core

# ---------- MAIN PIPELINE ----------
async def AIpipeline(problem: ProblemReq) -> Finalresult:
    cleaned = (problem.description or "")[:2400]
    session_id = problem.sessionId or "anon"
    cache_key = f"solver:{session_id}:{stable_hash(cleaned)}"

    try:
        cached = await redis_get_json(cache_key)
    except Exception as e:
        logger.warning("Redis get error for final cache: %s", e)
        cached = None

    if cached:
        try:
            return Finalresult(**cached)
        except Exception as e:
            logger.warning("Cached final result invalid: %s", e)

    # Controller
    try:
        ctrl_raw = await safe_model_call(
            gpt5_nano,
            MEGA_PROMPT.format(user_input=cleaned),
            timeout=MODEL_TIMEOUT_FAST,
            retries=1
        )
        ctrl = safe_json_loads(ctrl_raw) or fallback_ctrl()
    except Exception as e:
        logger.exception("Controller failure, using fallback: %s", e)
        ctrl = fallback_ctrl()

    # FIX: ensure defined
    use_rag = False

    try:
        use_rag = str(ctrl.get("complexity", "medium")) in ("medium", "high")
        context, retrieved_ids, rag_cache_hit = await retrieve_rag(problem, use_rag)
        if not isinstance(retrieved_ids, list):
            retrieved_ids = []
    except Exception as e:
        logger.warning("RAG retrieval failed: %s", e)
        context, retrieved_ids, rag_cache_hit = "", [], False

    complexity = ctrl.get("complexity", "medium") or "medium"
    confidence_ctrl = float(ctrl.get("confidence", CONF_DEFAULT) or CONF_DEFAULT)

    # smarter routing
    mode = "fast"
    if complexity == "medium":
        mode = "hybrid"
    if complexity == "high" or bool(ctrl.get("inconsistency_detected")) or confidence_ctrl < 0.45:
        mode = "deep"

    core = fallback_core(ctrl.get("draft_response") or cleaned, confidence_ctrl, retrieved_ids)

    deep_cache_key = f"deep:{stable_hash(cleaned + (context or ''))}"
    deep_cache = None
    deep_cache_hit = False

    try:
        deep_cache = await redis_get_json(deep_cache_key)
    except Exception:
        deep_cache = None

    if mode in ("hybrid", "deep"):
        if deep_cache:
            core = deep_cache
            deep_cache_hit = True
            logger.info("Deep cache hit")
        else:
            deep_prompt = f"""
Solve the problem step-by-step.
Return JSON:
{{
 "solution": "",
 "critique": "",
 "improvements": "",
 "reasoning": "",
 "confidence": 0.0,
 "sources": []
}}
PROBLEM:
{cleaned}
CONTEXT:
{context}
"""
            try:
                deep_raw = await safe_model_call(
                    deepseek_reasoner,
                    deep_prompt,
                    timeout=MODEL_TIMEOUT_DEEP,
                    retries=0
                )

                # ✅ timeout fallback
                if not deep_raw:
                    core = fallback_core(cleaned, confidence_ctrl, retrieved_ids)
                else:
                    parsed = safe_json_loads(deep_raw)
                    if parsed and parsed.get("solution"):
                        core = parsed
                    else:
                        core = fallback_core(cleaned, confidence_ctrl, retrieved_ids)

            except Exception as e:
                logger.exception("Deep reasoning failed: %s", e)
                core = fallback_core(cleaned, confidence_ctrl, retrieved_ids)

            # safe cache write
            try:
                if core.get("solution") and len(core.get("solution", "")) > 5:
                    await redis_set_json(deep_cache_key, core, ttl_seconds=DEEP_CACHE_TTL)
            except Exception as e:
                logger.warning("Failed to set deep cache: %s", e)

    # Reflection
    try:
        refine_prompt = f"Improve solution + add uncertainty + next_step:\n{json.dumps(core)}"
        refined_raw = await safe_model_call(gpt5_nano, refine_prompt, timeout=MODEL_TIMEOUT_FAST, retries=0)
        refined = safe_json_loads(refined_raw)

        # accept only if better
        if refined and refined.get("solution"):
            if len(refined.get("solution", "")) >= len(core.get("solution", "")):
                core = refined
    except Exception as e:
        logger.debug("Reflection step failed: %s", e)

    # Graph updates (unchanged)
    try:
        signal_raw = await safe_model_call(gpt5_nano, f"Extract entities/dependencies JSON:\n{cleaned}", timeout=MODEL_TIMEOUT_FAST, retries=0)
        signal = safe_json_loads(signal_raw) or {}
        if signal and problem.sessionId:
            signal["timestamp"] = now().isoformat()
            await update_graph(problem.sessionId, signal)
    except Exception:
        pass

    try:
        if any(k in cleaned.lower() for k in ["class", "function", "api", "repo"]):
            code_raw = await safe_model_call(gpt5_nano, f"Extract code structure JSON:\n{cleaned}", timeout=MODEL_TIMEOUT_FAST, retries=0)
            code_data = safe_json_loads(code_raw) or {}
            if code_data and problem.sessionId:
                await update_code_graph(problem.sessionId, code_data)
    except Exception:
        pass

    # AUTO EVOLVE
    try:
        core = await auto_evolve(core)
    except Exception:
        pass

    core_conf = min(max(float(core.get("confidence", CONF_DEFAULT)), 0.0), 0.92)

    result = Finalresult(
        Status="ok",
        OptimisedSolution=core.get("solution"),
        Critique=core.get("critique"),
        Improvements=core.get("improvements"),
        Confidence=core_conf,
        Rationale=f"intent={ctrl.get('intent')} | mode={mode}",
        Iteration=2 if mode == "deep" else 1,
        Created_At=now(),
        DeepCore=core.get("reasoning", ""),
        UsedRag=bool(use_rag),
        UsedDeep=mode in ("hybrid", "deep"),
        RagCacheHit=bool(rag_cache_hit),
        DeepCacheHit=bool(deep_cache_hit),
        ProblemKey=cache_key,
        RetrievedKnowledgeIds=core.get("sources") or retrieved_ids
    )

    try:
        await redis_set_json(cache_key, result.__dict__, ttl_seconds=FINAL_CACHE_TTL)
    except Exception as e:
        logger.warning("Failed to set final cache: %s", e)

    return result