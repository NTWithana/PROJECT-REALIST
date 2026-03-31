import os
import re
import json
import hashlib
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

import httpx
from dotenv import load_dotenv

# Redis (async)
try:
    from redis.asyncio import Redis
except Exception:
    Redis = None  # type: ignore

load_dotenv()
logger = logging.getLogger(__name__)


# CONFIG

REALIST_API_URL = os.getenv("REALIST_API_URL", "").rstrip("/")

# ChatSignals endpoints in RealistAPI
CHAT_SIGNALS_WRITE_URL = os.getenv("REALIST_CHAT_SIGNALS_WRITE_URL", "").rstrip("/")  # e.g. https://.../api/chat-signals
CHAT_SIGNALS_SEARCH_URL = os.getenv("REALIST_CHAT_SIGNALS_SEARCH_URL", "").rstrip("/")  # e.g. https://.../api/chat-signals/semantic-similar

REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_PREFIX = os.getenv("REDIS_PREFIX", "realist").strip()

CHAT_CACHE_TTL_SECONDS = int(os.getenv("CHAT_CACHE_TTL_SECONDS", "1800"))  # 30m
RAG_TTL_SECONDS = int(os.getenv("CHAT_RAG_TTL_SECONDS", "7200"))           # 2h

CONF_ESCALATE_TO_FLASH = float(os.getenv("CHAT_CONF_ESCALATE_TO_FLASH", "0.55"))
CONF_SKIP_RAG = float(os.getenv("CHAT_CONF_SKIP_RAG", "0.75"))
CONF_MIN_WRITE = float(os.getenv("CHAT_CONF_MIN_WRITE", "0.55"))

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "6.0"))
MODEL_TIMEOUT_LITE = float(os.getenv("MODEL_TIMEOUT_LITE_SECONDS", "8.0"))
MODEL_TIMEOUT_FLASH = float(os.getenv("MODEL_TIMEOUT_FLASH_SECONDS", "10.0"))

MAX_MSG_CHARS = int(os.getenv("CHAT_MAX_MSG_CHARS", "1400"))
MAX_CTX_CHARS = int(os.getenv("CHAT_MAX_CTX_CHARS", "1800"))
MAX_ANSWER_CHARS = int(os.getenv("CHAT_MAX_ANSWER_CHARS", "2000"))

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


async def flash_lite_chat(prompt: str) -> str:
    return f"[Flash-Lite] {prompt[:2000]}"

async def flash_chat(prompt: str) -> str:
    return f"[Flash] {prompt[:2000]}"


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

async def http_post(url: str, json_body: dict) -> Optional[httpx.Response]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            return await client.post(url, json=json_body)
    except Exception as e:
        logger.error(f"HTTP POST error: {url} | {e}")
        return None


# UTILS


def now() -> datetime:
    return datetime.utcnow()

def trim(text: str, limit: int) -> str:
    return (text or "")[:limit]

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def stable_key(*parts: str) -> str:
    raw = "||".join([p or "" for p in parts])
    return hashlib.md5(raw.encode()).hexdigest()

def parse_confidence(raw: str, default: float = 0.6) -> float:
    m = re.search(r"(0(?:\.\d+)?|1(?:\.0+)?)", raw or "")
    return clamp01(float(m.group(1))) if m else default

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

def clean_ids(ids: List[str]) -> List[str]:
    return [x for x in ids if x and isinstance(x, str)]

def redact_private_bits(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\b\d{12,19}\b", "[REDACTED_NUMBER]", text)
    text = re.sub(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*\S+", "[REDACTED_SECRET]", text)
    return text

# CANONICAL CHAT OUTPUT

def canonical_chat_output(
    *,
    response: str,
    confidence: float,
    mode: str,
    intent: str,
    model_used: str,
    used_global_rag: bool,
    used_chat_signals: bool,
    global_rag_cache_hit: bool,
    chat_signals_cache_hit: bool,
    retrieved_global_knowledge_ids: List[str],
    retrieved_chat_signal_ids: List[str],
    wrote_signal: bool,
    signal_ref: Optional[str],
    cache_hit: bool,
) -> Dict[str, Any]:
    return {
        "response": trim(response, MAX_ANSWER_CHARS),
        "confidence": clamp01(confidence),
        "mode": mode,
        "intent": intent,
        "model_used": model_used,
        "used_global_rag": bool(used_global_rag),
        "used_chat_signals": bool(used_chat_signals),
        "global_rag_cache_hit": bool(global_rag_cache_hit),
        "chat_signals_cache_hit": bool(chat_signals_cache_hit),
        "retrieved_global_knowledge_ids": clean_ids(retrieved_global_knowledge_ids),
        "retrieved_chat_signal_ids": clean_ids(retrieved_chat_signal_ids),
        "wrote_signal": bool(wrote_signal),
        "signal_ref": signal_ref,
        "cache_hit": bool(cache_hit),
    }

# ROUTER (FLASH-LITE)


async def route_chat(message: str, mode: str) -> Dict[str, Any]:
    prompt = f"""
Return JSON only:
{{
  "mode": "{mode}",
  "intent": "chat|hub|supervision|explain|summarize|plan|decide|research",
  "use_global_rag": true|false,
  "use_chat_signals": true|false,
  "escalate_to_flash": true|false,
  "confidence": 0.0-1.0,
  "memory_write": true|false
}}

Rules:
- hub: never reference private session data
- supervision: focus on continuity, risks, improvements, next actions
- chat: keep it fast and minimal

MESSAGE:
{message}
"""
    raw = await safe_call(flash_lite_chat, prompt, timeout=MODEL_TIMEOUT_LITE)
    data = safe_json_loads(raw) or {}
    return {
        "mode": data.get("mode", mode),
        "intent": data.get("intent", "chat"),
        "use_global_rag": bool(data.get("use_global_rag", True)),
        "use_chat_signals": bool(data.get("use_chat_signals", True)),
        "escalate_to_flash": bool(data.get("escalate_to_flash", False)),
        "confidence": clamp01(float(data.get("confidence", 0.6) or 0.6)),
        "memory_write": bool(data.get("memory_write", False)),
    }

# GLOBAL KNOWLEDGE RAG (READ)


async def retrieve_global_rag(query: str, domain: Optional[str], tags: Optional[List[str]]) -> Tuple[str, List[str], bool]:
    if not REALIST_API_URL:
        return "", [], False

    key = f"{REDIS_PREFIX}:chat:global_rag:{stable_key(query, domain or '', ','.join(tags or []))}"
    cached = await redis_get_json(key)
    if cached:
        return cached.get("context", ""), cached.get("ids", []), True

    params = {"query": query}
    if domain:
        params["domain"] = domain
    if tags:
        params["tags"] = tags

    res = await http_get(f"{REALIST_API_URL}/api/knowledge/semantic-similar", params=params)
    if not res or res.status_code != 200:
        return "", [], False

    data = (res.json() or [])[:8]
    ids: List[str] = []
    lines: List[str] = []
    for x in data:
        kid = x.get("id")
        if kid:
            ids.append(kid)
        lines.append(
            f"- ID: {kid}\n"
            f"  Problem: {trim(x.get('problem_summary',''), 220)}\n"
            f"  Solution: {trim(x.get('solution_summary',''), 320)}\n"
            f"  Conf: {x.get('confidence', 0)} | Reused: {x.get('reused_count', 0)} | Approved: {x.get('approved_count', 0)}"
        )

    context = trim("\n".join(lines), MAX_CTX_CHARS)

    await redis_set_json(
        key,
        {"context": context, "ids": ids, "ts": now().isoformat() + "Z"},
        ttl_seconds=RAG_TTL_SECONDS,
    )

    return context, ids, False


# CHAT SIGNALS RAG (READ)


async def retrieve_chat_signals(query: str, domain: Optional[str], tags: Optional[List[str]]) -> Tuple[str, List[str], bool]:
    if not CHAT_SIGNALS_SEARCH_URL:
        return "", [], False

    key = f"{REDIS_PREFIX}:chat:signals_rag:{stable_key(query, domain or '', ','.join(tags or []))}"
    cached = await redis_get_json(key)
    if cached:
        return cached.get("context", ""), cached.get("ids", []), True

    params = {"query": query}
    if domain:
        params["domain"] = domain
    if tags:
        params["tags"] = tags

    res = await http_get(CHAT_SIGNALS_SEARCH_URL, params=params)
    if not res or res.status_code != 200:
        return "", [], False

    data = (res.json() or [])[:8]
    ids: List[str] = []
    lines: List[str] = []
    for x in data:
        sid = x.get("id") or x.get("signalId")
        if sid:
            ids.append(sid)
        lines.append(
            f"- SignalID: {sid}\n"
            f"  Category: {x.get('category','')}\n"
            f"  Pattern: {trim(x.get('pattern',''), 260)}\n"
            f"  Importance: {x.get('importance', 0)}"
        )

    context = trim("\n".join(lines), 1200)

    await redis_set_json(
        key,
        {"context": context, "ids": ids, "ts": now().isoformat() + "Z"},
        ttl_seconds=RAG_TTL_SECONDS,
    )

    return context, ids, False


# SIGNAL EXTRACTION (EVOLUTION)


async def extract_signal(message: str, response: str) -> Dict[str, Any]:
    prompt = f"""
Extract reusable structured insight from the chat.
Return JSON only:
{{
  "pattern": "...",
  "category": "preference|workflow|pain_point|decision_rule|principle|constraint",
  "importance": 0.0-1.0,
  "tags": ["...","..."]
}}

Rules:
- pattern must be reusable (not a one-off)
- do not include secrets or private identifiers

MESSAGE:
{message}

RESPONSE:
{response}
"""
    raw = await safe_call(flash_lite_chat, prompt, timeout=MODEL_TIMEOUT_LITE)
    data = safe_json_loads(raw) or {}
    pattern = trim(redact_private_bits(str(data.get("pattern") or "")), 500) or None
    category = str(data.get("category") or "unknown")
    try:
        importance = clamp01(float(data.get("importance", 0.5)))
    except Exception:
        importance = 0.5
    tags = data.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    tags = [str(t) for t in tags if isinstance(t, (str, int, float))][:12]
    return {"pattern": pattern, "category": category, "importance": importance, "tags": tags}

async def write_chat_signal(payload: Dict[str, Any]) -> bool:
    if not CHAT_SIGNALS_WRITE_URL:
        return False
    res = await http_post(CHAT_SIGNALS_WRITE_URL, json_body=payload)
    return bool(res and res.status_code in (200, 201, 204))

# CHAT PIPELINE


async def chat_pipeline(
    message: str,
    *,
    mode: str = "chat",
    domain: str = "general",
    tags: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:

    msg = trim(redact_private_bits(message or ""), MAX_MSG_CHARS)
    tags = tags or []

    # Redis response cache (big cost saver)
    cache_key = f"{REDIS_PREFIX}:chat:final:{stable_key(mode, domain, ','.join(tags), msg)}"
    cached = await redis_get_json(cache_key)
    if cached and isinstance(cached, dict) and cached.get("out"):
        out = cached["out"]
        out["cache_hit"] = True
        return out

    route = await route_chat(msg, mode=mode)

    force_rag = route["intent"] in ("research", "plan", "decide")
    use_global_rag = bool(route["use_global_rag"] or force_rag)
    use_chat_signals = bool(route["use_chat_signals"])

    if route["intent"] == "chat" and route["confidence"] >= CONF_SKIP_RAG:
        use_global_rag = False
        use_chat_signals = False

    global_ctx, global_ids, global_cache_hit = await retrieve_global_rag(
        query=msg,
        domain=domain if domain else None,
        tags=tags if tags else None,
    ) if use_global_rag else ("", [], False)

    chat_ctx, chat_ids, chat_cache_hit = await retrieve_chat_signals(
        query=msg,
        domain=domain if domain else None,
        tags=tags if tags else None,
    ) if use_chat_signals else ("", [], False)

    system = {
        "chat": "You are Catalyst OS chat—fast, helpful, minimal fluff.",
        "hub": "You are the Realist Global Hub Assistant. Use global knowledge summaries; never reference private session data.",
        "supervision": "You are the session supervisor. Suggest improvements, detect risks, propose next actions, and keep continuity across sessions.",
    }.get(mode, "You are a helpful assistant.")

    base_prompt = f"""
SYSTEM:
{system}

INTENT:
{route.get("intent")}

USER MESSAGE:
{msg}

CHAT SIGNALS MEMORY (patterns, preferences, rules):
{chat_ctx}

GLOBAL KNOWLEDGE (summaries, solutions):
{global_ctx}

Return:
1) Direct response
2) Up to 3 next-actions (bullets) if relevant
3) One short 'why this' explanation
"""

    if route["escalate_to_flash"] or route["confidence"] < CONF_ESCALATE_TO_FLASH:
        model_used = "flash"
        answer = await safe_call(flash_chat, base_prompt, timeout=MODEL_TIMEOUT_FLASH)
    else:
        model_used = "flash_lite"
        answer = await safe_call(flash_lite_chat, base_prompt, timeout=MODEL_TIMEOUT_LITE)

    answer = trim(answer, MAX_ANSWER_CHARS)

    conf_raw = await safe_call(
        flash_lite_chat,
        f"Return only a number 0-1.\nANSWER:\n{answer}",
        timeout=MODEL_TIMEOUT_LITE,
    )
    confidence = parse_confidence(conf_raw, default=float(route.get("confidence", 0.6)))

    signal = await extract_signal(msg, answer)

    should_write = (
        (route.get("memory_write") or mode in ("hub", "supervision"))
        and confidence >= CONF_MIN_WRITE
        and bool(signal.get("pattern"))
        and float(signal.get("importance", 0.0)) >= 0.45
    )

    wrote_signal = False
    signal_ref = None

    if should_write:
        dedup_key = stable_key("signal", mode, domain, signal.get("category") or "", signal.get("pattern") or "")
        payload = {
            "dedupKey": dedup_key,
            "mode": mode,
            "intent": route.get("intent"),
            "domain": domain,
            "tags": list(set(tags + (signal.get("tags") or [])))[:20],
            "sessionId": session_id,
            "userId": user_id,
            "category": signal.get("category"),
            "pattern": signal.get("pattern"),
            "importance": signal.get("importance"),
            "message": msg,
            "response": trim(redact_private_bits(answer), 1200),
            "confidence": confidence,
            "modelUsed": model_used,
            "retrievedGlobalKnowledgeIds": clean_ids(global_ids),
            "retrievedChatSignalIds": clean_ids(chat_ids),
            "createdAt": now().isoformat() + "Z",
        }
        wrote_signal = await write_chat_signal(payload)
        if wrote_signal:
            signal_ref = dedup_key

    out = canonical_chat_output(
        response=answer,
        confidence=confidence,
        mode=mode,
        intent=str(route.get("intent") or "chat"),
        model_used=model_used,
        used_global_rag=use_global_rag,
        used_chat_signals=use_chat_signals,
        global_rag_cache_hit=global_cache_hit,
        chat_signals_cache_hit=chat_cache_hit,
        retrieved_global_knowledge_ids=global_ids,
        retrieved_chat_signal_ids=chat_ids,
        wrote_signal=wrote_signal,
        signal_ref=signal_ref,
        cache_hit=False,
    )

    await redis_set_json(
        cache_key,
        {"out": out, "ts": now().isoformat() + "Z"},
        ttl_seconds=CHAT_CACHE_TTL_SECONDS,
    )

    return out
