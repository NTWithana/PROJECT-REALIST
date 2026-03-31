import os
import re
import json
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List

import httpx
from dotenv import load_dotenv
from Models import ProblemReq, Finalresult

load_dotenv()
logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(hours=6)
RAG_TTL = timedelta(hours=2)

CONF_SKIP_DEEP = 0.70
MAX_CACHE_SIZE = 500

DEEP_CACHE: Dict[str, Dict[str, Any]] = {}
RAG_CACHE: Dict[str, Dict[str, Any]] = {}

# MODELS 

async def flash_chat(prompt: str) -> str:
    return f"[Flash] {prompt[:1200]}"

async def deepseek_reasoner(prompt: str) -> str:
    return f"[Deep] {prompt[:2000]}"

async def safe_call(fn, *args, timeout=10):
    try:
        return await asyncio.wait_for(fn(*args), timeout=timeout)
    except Exception as e:
        logger.error(f"Model error: {e}")
        return ""

#  UTILS 

def now():
    return datetime.utcnow()

def trim(text, limit=800):
    return (text or "")[:limit]

def cache_key(problem: ProblemReq):
    raw = f"{problem.description}-{getattr(problem,'domain',None)}-{getattr(problem,'tags',None)}"
    return hashlib.md5(raw.encode()).hexdigest()

def is_fresh(ts, ttl):
    return (now() - ts) < ttl

def clamp01(x):
    return max(0.0, min(1.0, x))

def parse_confidence(raw):
    m = re.search(r"(0(?:\.\d+)?|1(?:\.0+)?)", raw or "")
    return clamp01(float(m.group(1))) if m else 0.6

def evict_if_needed(cache):
    if len(cache) > MAX_CACHE_SIZE:
        oldest = sorted(cache.items(), key=lambda x: x[1]["ts"])[0][0]
        cache.pop(oldest, None)

def is_complex(text):
    t = text.lower()
    return len(t) > 300 or any(k in t for k in ["architecture","distributed","pipeline","rag"])

def clean_ids(ids):
    return [x for x in ids if x and isinstance(x, str)]

# ANALYSIS 
async def analyze_problem(text):
    raw = await safe_call(flash_chat, text)
    return "solve", True  # simplified fallback-safe

# RAG

async def retrieve_rag(problem, use_rag):
    if not use_rag:
        return "", []

    key = cache_key(problem)
    cached = RAG_CACHE.get(key)

    if cached and is_fresh(cached["ts"], RAG_TTL):
        return cached["data"], cached["ids"]

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(
                f"{os.getenv('REALIST_API_URL')}/api/knowledge/semantic-similar",
                params={"query": problem.description}
            )

            if res.status_code != 200:
                return "", []

            data = sorted(
                res.json(),
                key=lambda x: (x.get("reused_count", 0)*2 + x.get("approved_count", 0)),
                reverse=True
            )[:10]

            ids = []
            lines = []

            for x in data:
                kid = x.get("id")
                if kid:
                    ids.append(kid)

                lines.append(
                    f"- ID:{kid} | Reuse:{x.get('reused_count',0)} | Approved:{x.get('approved_count',0)}\n"
                    f"  {x.get('solution_summary','')}"
                )

            context = "\n".join(lines)

            RAG_CACHE[key] = {"data": context, "ids": ids, "ts": now()}
            evict_if_needed(RAG_CACHE)

            return context, ids

    except Exception as e:
        logger.error(f"RAG error: {e}")
        return "", []

# DEEP 

async def get_deep(problem, cleaned, context):
    raw = await safe_call(deepseek_reasoner, cleaned + context)

    try:
        return json.loads(raw)
    except:
        return {"core": raw, "used_knowledge_ids": []}

# PIPELINE 

async def hive_pipeline(problem: ProblemReq):
    cleaned = trim(problem.description)

    intent, use_rag = await analyze_problem(cleaned)
    context, retrieved_ids = await retrieve_rag(problem, use_rag)

    draft = await safe_call(flash_chat, cleaned + context)

    conf = parse_confidence(await safe_call(flash_chat, draft))

    if conf >= CONF_SKIP_DEEP and not is_complex(cleaned):
        core = draft
        used_ids = []
    else:
        deep = await get_deep(problem, cleaned, context)
        core = deep.get("core") or draft
        used_ids = deep.get("used_knowledge_ids") or retrieved_ids

    final = await safe_call(flash_chat, core)

    final_conf = clamp01(max(conf, parse_confidence(await safe_call(flash_chat, final))))

    return final, final_conf, {
        "used_ids": clean_ids(used_ids),
        "intent": intent,
        "used_rag": use_rag,
        "used_deep": conf < CONF_SKIP_DEEP
    }

# ENTRY 

async def AIpipeline(problem: ProblemReq) -> Finalresult:
    final, confidence, meta = await hive_pipeline(problem)

    return Finalresult(
        Status="ok",
        OptimisedSolution=final,
        Confidence=confidence,
        Rationale=f"intent={meta['intent']} | rag={meta['used_rag']}",
        Iteration=1,
        Created_At=now(),
        RetrievedKnowledgeIds=meta["used_ids"]
    )