import os
import re
import json
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional

import httpx
from dotenv import load_dotenv

from Models import ProblemReq, Finalresult

# Redis (async)
try:
    from redis.asyncio import Redis
except Exception:
    Redis = None  # type: ignore

load_dotenv()
logger = logging.getLogger(__name__)


# CONFIG


CACHE_TTL_SECONDS = int(os.getenv("AI_SOLVER_CACHE_TTL_SECONDS", "21600"))  # 6h
RAG_TTL_SECONDS = int(os.getenv("AI_SOLVER_RAG_TTL_SECONDS", "7200"))       # 2h

CONF_SKIP_DEEP = float(os.getenv("AI_SOLVER_CONF_SKIP_DEEP", "0.70"))
CONF_DEFAULT = float(os.getenv("AI_SOLVER_CONF_DEFAULT", "0.60"))

REALIST_API_URL = os.getenv("REALIST_API_URL", "").rstrip("/")

REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_PREFIX = os.getenv("REDIS_PREFIX", "realist").strip()

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "6.0"))
MODEL_TIMEOUT_FLASH = float(os.getenv("MODEL_TIMEOUT_FLASH_SECONDS", "10.0"))
MODEL_TIMEOUT_DEEP = float(os.getenv("MODEL_TIMEOUT_DEEP_SECONDS", "18.0"))

MAX_DESC_CHARS = int(os.getenv("AI_SOLVER_MAX_DESC_CHARS", "2400"))
MAX_CTX_CHARS = int(os.getenv("AI_SOLVER_MAX_CTX_CHARS", "2200"))
MAX_FINAL_CHARS = int(os.getenv("AI_SOLVER_MAX_FINAL_CHARS", "4000"))


# REDIS


_redis: Optional["Redis"] = None

def _redis_enabled() -> bool:
    return bool(REDIS_URL) and Redis is not None

async def redis_client() -> Optional["Redis"]:
    global _redis
    if not _redis_enabled():
        return None
    if _redis is None:
        _redis = Redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis

async def redis_get_json(key: str) -> Optional[dict]:
    r = await redis_client()
    if not r:
        return None
    try:
        raw = await r.get(key)
        if not raw:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None

async def redis_set_json(key: str, value: dict, ttl_seconds: int) -> None:
    r = await redis_client()
    if not r:
        return
    try:
        await r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)
    except Exception as e:
        logger.error(f"Redis set error: {e}")

# MODEL STUBS (REPLACE)


async def flash_chat(prompt: str) -> str:
    return f"[Flash] {prompt[:2000]}"

async def deepseek_reasoner(prompt: str) -> str:
    return f"[Deep] {prompt[:4000]}"


# SAFE CALLS


async def safe_call(fn, *args, timeout: float):
    try:
        return await asyncio.wait_for(fn(*args), timeout=timeout)
    except Exception as e:
        logger.error(f"Model error: {e}")
        return ""

async def http_get(url: str, params: dict) -> Optional[httpx.Response]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            return await client.get(url, params=params)
    except Exception as e:
        logger.error(f"HTTP GET error: {url} | {e}")
        return None


# UTILS


def now() -> datetime:
    return datetime.utcnow()

def trim(text: str, limit: int) -> str:
    return (text or "")[:limit]

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def parse_confidence(raw: str, default: float = CONF_DEFAULT) -> float:
    m = re.search(r"(0(?:\.\d+)?|1(?:\.0+)?)", raw or "")
    return clamp01(float(m.group(1))) if m else default

def stable_key(*parts: str) -> str:
    raw = "||".join([p or "" for p in parts])
    return hashlib.md5(raw.encode()).hexdigest()

def cache_key(problem: ProblemReq) -> str:
    return stable_key(
        "solver",
        trim(problem.description or "", 2000),
        str(getattr(problem, "domain", "") or ""),
        ",".join(getattr(problem, "tags", []) or []),
        str(getattr(problem, "sessionId", "") or ""),
    )

def is_complex(text: str) -> bool:
    t = (text or "").lower()
    return len(t) > 500 or any(k in t for k in ["architecture", "distributed", "pipeline", "rag", "design", "system"])

def clean_ids(ids: List[str]) -> List[str]:
    return [x for x in ids if x and isinstance(x, str)]

def strip_code_fences(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()

def safe_json_loads(raw: str) -> Optional[dict]:
    raw = strip_code_fences(raw or "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None


# CANONICAL OUTPUT SCHEMA


def canonical_solver_output(
    *,
    solution: str,
    critique: str = "",
    improvements: str = "",
    reasoning: str = "",
    confidence: float = CONF_DEFAULT,
    sources: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "solution": trim(solution, MAX_FINAL_CHARS),
        "critique": trim(critique, 1600),
        "improvements": trim(improvements, 1600),
        "reasoning": trim(reasoning, 2000),
        "confidence": clamp01(confidence),
        "sources": clean_ids(sources or []),
    }

async def enforce_solver_schema_from_model(raw: str, fallback_solution: str, fallback_sources: List[str]) -> Dict[str, Any]:
    data = safe_json_loads(raw)
    if not data:
        return canonical_solver_output(
            solution=fallback_solution,
            confidence=CONF_DEFAULT,
            sources=fallback_sources,
        )

    solution = data.get("solution") or data.get("core") or data.get("answer") or fallback_solution
    critique = data.get("critique") or ""
    improvements = data.get("improvements") or ""
    reasoning = data.get("reasoning") or data.get("rationale") or ""
    conf = data.get("confidence")
    try:
        conf = float(conf) if conf is not None else CONF_DEFAULT
    except Exception:
        conf = CONF_DEFAULT

    sources = data.get("sources") or data.get("used_knowledge_ids") or fallback_sources
    if not isinstance(sources, list):
        sources = fallback_sources

    return canonical_solver_output(
        solution=str(solution),
        critique=str(critique),
        improvements=str(improvements),
        reasoning=str(reasoning),
        confidence=clamp01(conf),
        sources=sources,
    )


# ANALYSIS


async def analyze_problem(text: str) -> Tuple[str, bool]:
    # Keep your behavior, but make it deterministic + safe
    # intent: "solve" | "explain" | "plan" etc (v1: solve)
    return "solve", True


# RAG (GLOBAL KNOWLEDGE READ)


async def retrieve_rag(problem: ProblemReq, use_rag: bool) -> Tuple[str, List[str], bool]:
    if not use_rag or not REALIST_API_URL:
        return "", [], False

    key = f"{REDIS_PREFIX}:solver:rag:{cache_key(problem)}"
    cached = await redis_get_json(key)
    if cached:
        return cached.get("context", ""), cached.get("ids", []), True

    res = await http_get(
        f"{REALIST_API_URL}/api/knowledge/semantic-similar",
        params={"query": problem.description, "domain": problem.domain, "tags": problem.tags},
    )
    if not res or res.status_code != 200:
        return "", [], False

    items = (res.json() or [])[:10]

    # Slightly better ranking than reused*2 + approved:
    # score = approved*2 + reused*1.5 + confidence*1 + recency_bonus
    def score(x: dict) -> float:
        approved = float(x.get("approved_count", 0) or 0)
        reused = float(x.get("reused_count", 0) or 0)
        conf = float(x.get("confidence", 0) or 0)
        # recency bonus (soft): newer gets a small bump if created_at exists
        recency = 0.0
        try:
            created = x.get("created_at")
            if created:
                # if ISO string, just reward presence; keep it simple and safe
                recency = 0.15
        except Exception:
            recency = 0.0
        return approved * 2.0 + reused * 1.5 + conf * 1.0 + recency

    items = sorted(items, key=score, reverse=True)[:10]

    ids: List[str] = []
    lines: List[str] = []
    for x in items:
        kid = x.get("id")
        if kid:
            ids.append(kid)
        lines.append(
            f"- ID: {kid} | Conf: {x.get('confidence', 0)} | Reused: {x.get('reused_count', 0)} | Approved: {x.get('approved_count', 0)}\n"
            f"  Problem: {trim(x.get('problem_summary',''), 240)}\n"
            f"  Solution: {trim(x.get('solution_summary',''), 520)}"
        )

    context = trim("\n".join(lines), MAX_CTX_CHARS)

    await redis_set_json(
        key,
        {"context": context, "ids": ids, "ts": now().isoformat() + "Z"},
        ttl_seconds=RAG_TTL_SECONDS,
    )

    return context, ids, False


# DEEP (STRUCTURED)

async def get_deep_structured(cleaned: str, context: str, retrieved_ids: List[str]) -> Dict[str, Any]:
    prompt = f"""
Return JSON only with this schema:
{{
  "solution": "...",
  "critique": "...",
  "improvements": "...",
  "reasoning": "...",
  "confidence": 0.0-1.0,
  "sources": ["knowledgeId1","knowledgeId2"]
}}

TASK:
Solve the user's problem. Use GLOBAL CONTEXT if helpful.
If you used any knowledge IDs, include them in "sources".

USER PROBLEM:
{cleaned}

GLOBAL CONTEXT:
{context}
"""
    raw = await safe_call(deepseek_reasoner, prompt, timeout=MODEL_TIMEOUT_DEEP)
    return await enforce_solver_schema_from_model(raw, fallback_solution="", fallback_sources=retrieved_ids)


# PIPELINE

async def hive_pipeline(problem: ProblemReq) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    cleaned = trim(problem.description or "", MAX_DESC_CHARS)

    intent, use_rag = await analyze_problem(cleaned)
    context, retrieved_ids, rag_cache_hit = await retrieve_rag(problem, use_rag)

    # Draft (fast)
    draft_prompt = f"""
Return JSON only with this schema:
{{
  "solution": "...",
  "critique": "...",
  "improvements": "...",
  "reasoning": "...",
  "confidence": 0.0-1.0,
  "sources": ["..."]
}}

USER PROBLEM:
{cleaned}

GLOBAL CONTEXT:
{context}
"""
    draft_raw = await safe_call(flash_chat, draft_prompt, timeout=MODEL_TIMEOUT_FLASH)
    draft = await enforce_solver_schema_from_model(draft_raw, fallback_solution=cleaned, fallback_sources=retrieved_ids)

    # Decide deep
    conf = float(draft.get("confidence", CONF_DEFAULT))
    use_deep = not (conf >= CONF_SKIP_DEEP and not is_complex(cleaned))

    if use_deep:
        deep = await get_deep_structured(cleaned, context, retrieved_ids)
        core = deep if deep.get("solution") else draft
    else:
        core = draft

    # Final polish (still structured)
    final_prompt = f"""
Return JSON only with this schema:
{{
  "solution": "...",
  "critique": "...",
  "improvements": "...",
  "reasoning": "...",
  "confidence": 0.0-1.0,
  "sources": ["..."]
}}

POLISH THIS OUTPUT (keep meaning, improve clarity):
{json.dumps(core, ensure_ascii=False)}
"""
    final_raw = await safe_call(flash_chat, final_prompt, timeout=MODEL_TIMEOUT_FLASH)
    final = await enforce_solver_schema_from_model(final_raw, fallback_solution=core.get("solution", ""), fallback_sources=core.get("sources", retrieved_ids))

    meta = {
        "intent": intent,
        "used_rag": bool(use_rag),
        "used_deep": bool(use_deep),
        "rag_cache_hit": bool(rag_cache_hit),
        "retrieved_ids": clean_ids(retrieved_ids),
    }
    return final, meta


# ENTRY (COMPATIBLE)


async def AIpipeline(problem: ProblemReq) -> Finalresult:
    # Redis full-result cache (optional but big cost saver)
    key = f"{REDIS_PREFIX}:solver:final:{cache_key(problem)}"
    cached = await redis_get_json(key)
    if cached and isinstance(cached, dict) and cached.get("final"):
        f = cached["final"]
        meta = cached.get("meta", {})
        return Finalresult(
            Status="ok",
            OptimisedSolution=f.get("solution"),
            Critique=f.get("critique"),
            Improvements=f.get("improvements"),
            Confidence=f.get("confidence"),
            Rationale=f"intent={meta.get('intent')} | rag={meta.get('used_rag')} | deep={meta.get('used_deep')} | cache=redis",
            Iteration=1,
            Created_At=now(),
            DeepCore=f.get("reasoning"),
            UsedRag=bool(meta.get("used_rag", False)),
            UsedDeep=bool(meta.get("used_deep", False)),
            RagCacheHit=bool(meta.get("rag_cache_hit", False)),
            RetrievedKnowledgeIds=clean_ids(f.get("sources", [])),
        )

    final, meta = await hive_pipeline(problem)

    out = Finalresult(
        Status="ok",
        OptimisedSolution=final.get("solution"),
        Critique=final.get("critique"),
        Improvements=final.get("improvements"),
        Confidence=final.get("confidence"),
        Rationale=f"intent={meta['intent']} | rag={meta['used_rag']} | deep={meta['used_deep']}",
        Iteration=1,
        Created_At=now(),
        DeepCore=final.get("reasoning"),
        UsedRag=bool(meta["used_rag"]),
        UsedDeep=bool(meta["used_deep"]),
        RagCacheHit=bool(meta["rag_cache_hit"]),
        RetrievedKnowledgeIds=clean_ids(final.get("sources", [])),
    )

    await redis_set_json(
        key,
        {"final": final, "meta": meta, "ts": now().isoformat() + "Z"},
        ttl_seconds=CACHE_TTL_SECONDS,
    )

    return out
