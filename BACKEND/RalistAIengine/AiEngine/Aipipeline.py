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
        # try to extract first JSON object
        try:
            import re
            m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass
    return None
async def safe_model_call(fn, *args, timeout: float, retries: int = 1):
    """Call model with timeout and optional retries. Return empty string on failure."""
    last_exc = None
    for attempt in range(retries + 1):
        try:
            # model functions in your code accept (prompt, timeout=...)
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
async def AIpipeline(problem: ProblemReq) -> Finalresult:
    cleaned = (problem.description or "")[:2400]
    session_id = problem.sessionId or "anon"
    cache_key = f"solver:{session_id}:{stable_hash(cleaned)}"
    # Try final-result cache
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
    # Controller (fast)
    try:
        ctrl_raw = await safe_model_call(gpt5_nano, MEGA_PROMPT.format(user_input=cleaned), timeout=MODEL_TIMEOUT_FAST, retries=1)
        ctrl = safe_json_loads(ctrl_raw) or fallback_ctrl()
    except Exception as e:
        logger.exception("Controller failure, using fallback: %s", e)
        ctrl = fallback_ctrl()
    # RAG retrieval (defensive)
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
    # Decide mode
    mode = "fast"
    if complexity == "medium":
        mode = "hybrid"
    if complexity == "high" or bool(ctrl.get("inconsistency_detected")):
        mode = "deep"
    core = fallback_core(ctrl.get("draft_response") or cleaned, confidence_ctrl, retrieved_ids)
    # Deep reasoning with caching
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
                deep_raw = await safe_model_call(deepseek_reasoner, deep_prompt, timeout=MODEL_TIMEOUT_DEEP, retries=0)
                parsed = safe_json_loads(deep_raw)
                if parsed and isinstance(parsed, dict) and parsed.get("solution"):
                    core = parsed
                else:
                    logger.warning("Deep model returned invalid JSON or missing solution; using fallback core")
                    core = fallback_core(ctrl.get("draft_response") or cleaned, ctrl.get("confidence", CONF_DEFAULT), retrieved_ids)
            except Exception as e:
                logger.exception("Deep reasoning failed: %s", e)
                core = fallback_core(ctrl.get("draft_response") or cleaned, ctrl.get("confidence", CONF_DEFAULT), retrieved_ids)
            # store deep result if valid
            try:
                await redis_set_json(deep_cache_key, core, ttl_seconds=DEEP_CACHE_TTL)
            except Exception as e:
                logger.warning("Failed to set deep cache: %s", e)
            deep_cache_hit = False
    else:
        deep_cache_hit = False
    # Reflection / polish (fast model)
    try:
        refine_prompt = f"Improve solution + add uncertainty + next_step:\n{json.dumps(core)}"
        refined_raw = await safe_model_call(gpt5_nano, refine_prompt, timeout=MODEL_TIMEOUT_FAST, retries=0)
        refined = safe_json_loads(refined_raw)
        if refined and isinstance(refined, dict) and refined.get("solution"):
            core = refined
    except Exception as e:
        logger.debug("Reflection step failed (non-fatal): %s", e)
    # Session graph update (non-blocking)
    try:
        signal_raw = await safe_model_call(gpt5_nano, f"Extract entities/dependencies JSON:\n{cleaned}", timeout=MODEL_TIMEOUT_FAST, retries=0)
        signal = safe_json_loads(signal_raw) or {}
        if signal and problem.sessionId:
            signal["timestamp"] = now().isoformat()
            try:
                await update_graph(problem.sessionId, signal)
            except Exception as e:
                logger.warning("update_graph failed: %s", e)
    except Exception as e:
        logger.debug("Session graph extraction failed: %s", e)
    # Code graph update (non-blocking)
    try:
        if any(k in (cleaned or "").lower() for k in ["class", "function", "api", "repo"]):
            code_raw = await safe_model_call(gpt5_nano, f"Extract code structure JSON:\n{cleaned}", timeout=MODEL_TIMEOUT_FAST, retries=0)
            code_data = safe_json_loads(code_raw) or {}
            if code_data and problem.sessionId:
                try:
                    await update_code_graph(problem.sessionId, code_data)
                except Exception as e:
                    logger.warning("update_code_graph failed: %s", e)
    except Exception as e:
        logger.debug("Code graph extraction failed: %s", e)
    # Normalize confidence and build result
    try:
        core_conf = float(core.get("confidence", CONF_DEFAULT) or CONF_DEFAULT)
    except Exception:
        core_conf = CONF_DEFAULT
    core_conf = min(max(core_conf, 0.0), 0.92)
    core_sources = core.get("sources") if isinstance(core.get("sources"), list) else retrieved_ids
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
        RetrievedKnowledgeIds=core_sources or []
    )
    # Cache final result
    try:
        await redis_set_json(cache_key, result.__dict__, ttl_seconds=FINAL_CACHE_TTL)
    except Exception as e:
        logger.warning("Failed to set final cache: %s", e)
    return result

