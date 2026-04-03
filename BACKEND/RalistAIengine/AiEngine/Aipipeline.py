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

def stable_hash(text: str):
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

async def AIpipeline(problem: ProblemReq) -> Finalresult:
    cleaned = (problem.description or "")[:2400]

    cache_key = f"solver:{problem.sessionId}:{stable_hash(cleaned)}"
    cached = await redis_get_json(cache_key)
    if cached:
        return Finalresult(**cached)

    # CONTROLLER 
    ctrl = safe_json_loads(
        await gpt5_nano(MEGA_PROMPT.format(user_input=cleaned), MODEL_TIMEOUT_FAST)
    ) or fallback_ctrl()

    # RAG 
    use_rag = ctrl.get("complexity") in ("medium", "high")
    context, retrieved_ids, rag_cache_hit = await retrieve_rag(problem, use_rag)

    complexity = ctrl.get("complexity", "medium")
    confidence = float(ctrl.get("confidence", CONF_DEFAULT))

    #  MODE 
    mode = "fast"
    if complexity == "medium":
        mode = "hybrid"
    if complexity == "high" or ctrl.get("inconsistency_detected"):
        mode = "deep"

    core = fallback_core(
        ctrl.get("draft_response") or cleaned,
        confidence,
        retrieved_ids
    )

    deep_cache_key = f"deep:{stable_hash(cleaned + context)}"
    deep_cache = await redis_get_json(deep_cache_key)

    # DEEP PROMPT 
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

    # HYBRID / DEEP
    if mode in ("hybrid", "deep"):
        if deep_cache:
            core = deep_cache
            deep_cache_hit = True
        else:
            deep1 = safe_json_loads(
                await deepseek_reasoner(deep_prompt, MODEL_TIMEOUT_DEEP)
            ) or core

            if mode == "deep":
                try:
                    deep2 = safe_json_loads(
                        await deepseek_reasoner(
                            f"Improve solution:\n{json.dumps(deep1)}",
                            MODEL_TIMEOUT_DEEP
                        )
                    )
                    core = deep2 if deep2 and "solution" in deep2 else deep1
                except:
                    core = deep1
            else:
                core = deep1

            await redis_set_json(deep_cache_key, core, 86400)
            deep_cache_hit = False
    else:
        deep_cache_hit = False

    # REFLECTION
    try:
        refined = safe_json_loads(
            await gpt5_nano(
                f"Improve solution + add uncertainty + next_step:\n{json.dumps(core)}",
                MODEL_TIMEOUT_FAST
            )
        )
        if refined and "solution" in refined:
            core = refined
    except:
        pass

    #  SESSION GRAPH
    try:
        signal = safe_json_loads(
            await gpt5_nano(f"Extract entities/dependencies JSON:\n{cleaned}")
        )
        if signal and problem.sessionId:
            signal["timestamp"] = now().isoformat()
            await update_graph(problem.sessionId, signal)
    except:
        pass

    # CODE GRAPH
    if any(k in cleaned.lower() for k in ["class", "function", "api", "repo"]):
        try:
            code_data = safe_json_loads(
                await gpt5_nano(f"Extract code structure JSON:\n{cleaned}")
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