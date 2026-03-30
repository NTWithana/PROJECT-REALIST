import os
import re
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

import httpx
from dotenv import load_dotenv
from Models import ProblemReq, Finalresult

load_dotenv()
logger = logging.getLogger(__name__)


# CONFIG

CACHE_TTL = timedelta(hours=6)
RAG_TTL = timedelta(hours=2)

CONF_SKIP_DEEP = 0.70
CONF_MIN_REFINE = 0.55

MAX_CACHE_SIZE = 500

DEEP_CACHE: Dict[str, Dict[str, Any]] = {}
RAG_CACHE: Dict[str, Dict[str, Any]] = {}

# Prevent deep overload
DEEP_LIMIT = asyncio.Semaphore(3)


# MODEL STUBS

async def flash_chat(prompt: str) -> str:
    return f"[Gemini-Flash] {prompt[:1200]}"

async def deepseek_reasoner(prompt: str) -> str:
    return f"[DeepSeek-Reasoner] {prompt[:2000]}"


# SAFE CALL

async def safe_call(fn, *args, timeout=8):
    try:
        return await asyncio.wait_for(fn(*args), timeout=timeout)
    except Exception as e:
        logger.error(f"{fn.__name__} failed: {e}")
        return ""


# UTILITIES

def now() -> datetime:
    return datetime.utcnow()

def trim(text: str, limit: int = 800) -> str:
    return (text or "")[:limit]

def cache_key(problem: ProblemReq, intent: str) -> str:
    raw = f"{problem.description}-{getattr(problem,'domain',None)}-{getattr(problem,'tags',None)}-{intent}"
    return hashlib.md5(raw.encode()).hexdigest()

def is_fresh(ts: datetime, ttl: timedelta) -> bool:
    return (now() - ts) < ttl

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def parse_confidence(raw: str) -> float:
    m = re.search(r"(0(?:\.\d+)?|1(?:\.0+)?)", raw or "")
    return clamp01(float(m.group(1))) if m else 0.6

def evict_if_needed(cache: Dict):
    if len(cache) > MAX_CACHE_SIZE:
        oldest = sorted(cache.items(), key=lambda x: x[1]["ts"])[0][0]
        cache.pop(oldest, None)


# MERGED FLASH GENERATION + CONFIDENCE 

async def flash_generate_with_conf(prompt: str):
    full_prompt = f"""
Answer the problem AND give confidence.

FORMAT:
ANSWER:
<your answer>

CONFIDENCE:
<number between 0 and 1>

PROBLEM:
{prompt}
"""
    raw = await safe_call(flash_chat, full_prompt)

    answer = raw.split("CONFIDENCE:")[0].replace("ANSWER:", "").strip()
    conf = parse_confidence(raw)

    return answer, conf


# FLASH ANALYSIS

async def analyze_problem(text: str):
    prompt = f"""
Return JSON only:
{{"intent":"solve|build|fix|research|analyze|plan|create|learn|explore|decide","use_rag":true|false}}

TEXT:
{text}
"""
    raw = await safe_call(flash_chat, prompt)

    intent = re.search(r'"intent"\s*:\s*"(\w+)"', raw)
    rag = re.search(r'"use_rag"\s*:\s*(true|false)', raw)

    return (
        intent.group(1) if intent else "solve",
        rag.group(1) == "true" if rag else False
    )


# RAG (improved signal)

async def retrieve_rag(problem: ProblemReq, intent: str, use_rag: bool) -> str:
    if not use_rag:
        return ""

    key = cache_key(problem, intent)
    cached = RAG_CACHE.get(key)

    if cached and is_fresh(cached["ts"], RAG_TTL):
        return cached["data"]

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(
                f"{os.getenv('REALIST_API_URL')}/api/knowledge/semantic-similar",
                params={"query": problem.description}
            )

            if res.status_code != 200:
                return ""

            data = res.json()[:5]

            raw_context = "\n".join([
                f"- Problem: {x.get('problem_summary','')}\n  Solution: {x.get('solution_summary','')}"
                for x in data
            ])

            # 🔥 compress RAG (Fix #3)
            context = await safe_call(flash_chat, f"Summarize key insights:\n{raw_context}")

            RAG_CACHE[key] = {"data": context, "ts": now()}
            evict_if_needed(RAG_CACHE)

            return context

    except Exception as e:
        logger.error(f"RAG error: {e}")
        return ""


# DEEP CORE (throttled)

async def get_deep_core(problem: ProblemReq, cleaned: str, context: str, intent: str) -> str:
    key = cache_key(problem, intent)
    cached = DEEP_CACHE.get(key)

    if cached and is_fresh(cached["ts"], CACHE_TTL):
        return cached["data"]

    prompt = f"""
Deep reasoning.

INTENT: {intent}

PROBLEM:
{cleaned}

CONTEXT:
{context}

Be structured, correct, and practical.
"""

    async with DEEP_LIMIT:
        result = await safe_call(deepseek_reasoner, prompt)

    DEEP_CACHE[key] = {"data": result, "ts": now()}
    evict_if_needed(DEEP_CACHE)

    return result


# PIPELINE

async def hive_pipeline(problem: ProblemReq):
    cleaned = trim(problem.description)

    intent, use_rag = await analyze_problem(cleaned)

    context = await retrieve_rag(problem, intent, use_rag)

    # Step 1 — Draft + confidence (merged)
    draft, conf = await flash_generate_with_conf(f"{cleaned}\n{context}")

    # Step 2 — Deep decision
    if conf >= CONF_SKIP_DEEP:
        core = draft
        used_deep = False
    else:
        core = await get_deep_core(problem, cleaned, context, intent)
        used_deep = True

    # Step 3 — Conditional refinement (Fix #2)
    if conf < CONF_MIN_REFINE:
        critique = await safe_call(flash_chat, f"Critique:\n{core}")
        improvements = await safe_call(flash_chat, f"Improve:\n{core}\n{critique}")
    else:
        critique = ""
        improvements = ""

    # Step 4 — Final synthesis
    final = await safe_call(flash_chat, f"""
FINAL ANSWER:

{core}

CRITIQUE:
{critique}

IMPROVEMENTS:
{improvements}

Produce best structured answer.
""")

    # Final confidence update (Fix #6)
    final_conf = parse_confidence(await safe_call(flash_chat, f"Score 0-1:\n{final}"))

    return final, clamp01(max(conf, final_conf))


# ENTRY

async def AIpipeline(problem: ProblemReq) -> Finalresult:
    try:
        final, confidence = await hive_pipeline(problem)

        return Finalresult(
            Status="ok",
            OptimisedSolution=final,
            Confidence=confidence,
            Rationale="Optimized hybrid pipeline (cost-efficient, gated deep reasoning, RAG-aware)",
            Iteration=1,
            Created_At=now()
        )

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

        return Finalresult(
            Status="error",
            OptimisedSolution="Something went wrong.",
            Confidence=0.3,
            Rationale=str(e),
            Iteration=0,
            Created_At=now()
        )