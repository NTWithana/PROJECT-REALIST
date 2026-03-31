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

load_dotenv()
logger = logging.getLogger(__name__)


# CONFIG


CHAT_CACHE_TTL = timedelta(minutes=30)
RAG_TTL = timedelta(hours=2)
MAX_CACHE_SIZE = 800

CONF_ESCALATE_TO_FLASH = 0.55
CONF_SKIP_RAG = 0.75
CONF_MIN_WRITE = 0.55  # don't write weak/noisy signals

# Caches
CHAT_CACHE: Dict[str, Dict[str, Any]] = {}
GLOBAL_RAG_CACHE: Dict[str, Dict[str, Any]] = {}
CHAT_RAG_CACHE: Dict[str, Dict[str, Any]] = {}

# URLs
REALIST_API_URL = os.getenv("REALIST_API_URL", "").rstrip("/")

# Separate ChatSignals system (recommended)
CHAT_SIGNALS_WRITE_URL = os.getenv("REALIST_CHAT_SIGNALS_WRITE_URL", "").rstrip("/")
CHAT_SIGNALS_SEARCH_URL = os.getenv("REALIST_CHAT_SIGNALS_SEARCH_URL", "").rstrip("/")

# MODEL STUBS (REPLACE)


async def flash_lite_chat(prompt: str) -> str:
    return f"[Flash-Lite] {prompt[:1200]}"

async def flash_chat(prompt: str) -> str:
    return f"[Flash] {prompt[:1200]}"

# SAFE CALL + RETRY


async def safe_call(fn, *args, timeout=8):
    try:
        return await asyncio.wait_for(fn(*args), timeout=timeout)
    except Exception as e:
        logger.error(f"Model error: {e}")
        return ""

async def http_call_with_retry(method: str, url: str, *, json_body=None, params=None, timeout=6.0, retries=2):
    last_err = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    return await client.get(url, params=params)
                if method.upper() == "POST":
                    return await client.post(url, json=json_body)
                raise ValueError("Unsupported method")
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.25 * (attempt + 1))
    logger.error(f"HTTP error after retries: {url} | {last_err}")
    return None


# UTILS


def now() -> datetime:
    return datetime.utcnow()

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def trim(text: str, limit: int = 1200) -> str:
    return (text or "")[:limit]

def is_fresh(ts: datetime, ttl: timedelta) -> bool:
    return (now() - ts) < ttl

def evict_if_needed(cache: Dict[str, Dict[str, Any]]):
    if len(cache) > MAX_CACHE_SIZE:
        oldest = sorted(cache.items(), key=lambda x: x[1]["ts"])[0][0]
        cache.pop(oldest, None)

def stable_key(*parts: str) -> str:
    raw = "||".join([p or "" for p in parts])
    return hashlib.md5(raw.encode()).hexdigest()

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
    except:
        # try to salvage first JSON object
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except:
            return None

def parse_confidence(raw: str, default: float = 0.6) -> float:
    # expects "0.73" or "CONFIDENCE: 0.73" etc
    m = re.search(r"(0(?:\.\d+)?|1(?:\.0+)?)", raw or "")
    return clamp01(float(m.group(1))) if m else default

def redact_private_bits(text: str) -> str:
    # lightweight guardrail: avoid accidentally persisting secrets
    if not text:
        return ""
    text = re.sub(r"\b\d{12,19}\b", "[REDACTED_NUMBER]", text)  # long numbers
    text = re.sub(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*\S+", "[REDACTED_SECRET]", text)
    return text

# ROUTER (FLASH-LITE)

async def route_chat(message: str, mode: str = "chat") -> Dict[str, Any]:
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
    raw = await safe_call(flash_lite_chat, prompt)
    data = safe_json_loads(raw)

    if not data:
        return {
            "mode": mode,
            "intent": "chat",
            "use_global_rag": True,
            "use_chat_signals": True,
            "escalate_to_flash": False,
            "confidence": 0.6,
            "memory_write": False
        }

    return {
        "mode": data.get("mode", mode),
        "intent": data.get("intent", "chat"),
        "use_global_rag": bool(data.get("use_global_rag", True)),
        "use_chat_signals": bool(data.get("use_chat_signals", True)),
        "escalate_to_flash": bool(data.get("escalate_to_flash", False)),
        "confidence": clamp01(float(data.get("confidence", 0.6))),
        "memory_write": bool(data.get("memory_write", False)),
    }


# GLOBAL KNOWLEDGE RAG (READ)


async def retrieve_global_rag(query: str, domain: Optional[str] = None, tags: Optional[List[str]] = None) -> Tuple[str, List[str], bool]:
    if not REALIST_API_URL:
        return "", [], False

    key = stable_key("global_rag", query, domain or "", ",".join(tags or []))
    cached = GLOBAL_RAG_CACHE.get(key)
    if cached and is_fresh(cached["ts"], RAG_TTL):
        return cached["context"], cached.get("ids", []), True

    params = {"query": query}
    if domain:
        params["domain"] = domain
    if tags:
        params["tags"] = tags

    res = await http_call_with_retry("GET", f"{REALIST_API_URL}/api/knowledge/semantic-similar", params=params)
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
            f"  Confidence: {x.get('confidence', 0)} | Reused: {x.get('reused_count', 0)} | Approved: {x.get('approved_count', 0)}"
        )

    context = trim("\n".join(lines), 1600)
    GLOBAL_RAG_CACHE[key] = {"context": context, "ids": ids, "ts": now()}
    evict_if_needed(GLOBAL_RAG_CACHE)

    return context, ids, False

# =========================
# CHAT SIGNALS RAG (READ) - OPTIONAL
# =========================

async def retrieve_chat_signals(query: str, domain: Optional[str] = None, tags: Optional[List[str]] = None) -> Tuple[str, List[str], bool]:
    if not CHAT_SIGNALS_SEARCH_URL:
        return "", [], False

    key = stable_key("chat_rag", query, domain or "", ",".join(tags or []))
    cached = CHAT_RAG_CACHE.get(key)
    if cached and is_fresh(cached["ts"], RAG_TTL):
        return cached["context"], cached.get("ids", []), True

    params = {"query": query}
    if domain:
        params["domain"] = domain
    if tags:
        params["tags"] = tags

    res = await http_call_with_retry("GET", CHAT_SIGNALS_SEARCH_URL, params=params)
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
    CHAT_RAG_CACHE[key] = {"context": context, "ids": ids, "ts": now()}
    evict_if_needed(CHAT_RAG_CACHE)

    return context, ids, False

# =========================
# SIGNAL EXTRACTION (STRUCTURED EVOLUTION)
# =========================

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
    raw = await safe_call(flash_lite_chat, prompt)
    data = safe_json_loads(raw)

    if not data:
        return {"pattern": None, "category": "unknown", "importance": 0.5, "tags": []}

    return {
        "pattern": trim(redact_private_bits(str(data.get("pattern") or "")), 500) or None,
        "category": str(data.get("category") or "unknown"),
        "importance": clamp01(float(data.get("importance", 0.5))),
        "tags": [str(t) for t in (data.get("tags") or []) if isinstance(t, (str, int, float))][:12],
    }


# WRITE-BACK (CHAT SIGNALS)


async def write_chat_signal(payload: Dict[str, Any]) -> bool:
    if not CHAT_SIGNALS_WRITE_URL:
        return False
    res = await http_call_with_retry("POST", CHAT_SIGNALS_WRITE_URL, json_body=payload)
    return bool(res and res.status_code in (200, 201, 204))


# CHAT PIPELINE


async def chat_pipeline(
    message: str,
    *,
    mode: str = "chat",
    domain: str = "general",
    tags: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:

    msg = trim(redact_private_bits(message), 1200)
    tags = tags or []

    ckey = stable_key("chat", mode, domain, ",".join(tags), msg)
    cached = CHAT_CACHE.get(ckey)
    if cached and is_fresh(cached["ts"], CHAT_CACHE_TTL):
        return {**cached["data"], "cache_hit": True}

    route = await route_chat(msg, mode=mode)

    # Force RAG for certain intents
    force_rag = route["intent"] in ("research", "plan", "decide")
    use_global_rag = bool(route["use_global_rag"] or force_rag)
    use_chat_signals = bool(route["use_chat_signals"])

    # Skip RAG for simple chat if confident
    if route["intent"] == "chat" and route["confidence"] >= CONF_SKIP_RAG:
        use_global_rag = False
        use_chat_signals = False

    global_ctx, global_ids, global_cache_hit = await retrieve_global_rag(
        query=msg,
        domain=domain if domain else None,
        tags=tags if tags else None
    ) if use_global_rag else ("", [], False)

    chat_ctx, chat_ids, chat_cache_hit = await retrieve_chat_signals(
        query=msg,
        domain=domain if domain else None,
        tags=tags if tags else None
    ) if use_chat_signals else ("", [], False)

    system = {
        "chat": "You are Catalyst OS chat—fast, helpful, minimal fluff.",
        "hub": "You are the Realist Global Hub Assistant. Use global knowledge summaries; never reference private session data.",
        "supervision": "You are the session supervisor. Suggest improvements, detect risks, propose next actions, and keep continuity across sessions."
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

    # Escalation logic
    if route["escalate_to_flash"] or route["confidence"] < CONF_ESCALATE_TO_FLASH:
        model_used = "flash"
        answer = await safe_call(flash_chat, base_prompt, timeout=10)
    else:
        model_used = "flash_lite"
        answer = await safe_call(flash_lite_chat, base_prompt, timeout=8)

    answer = trim(answer, 1600)

    # Confidence scoring (lite is fine)
    conf_raw = await safe_call(
        flash_lite_chat,
        f"Return only a number 0-1.\nANSWER:\n{answer}",
        timeout=6
    )
    confidence = parse_confidence(conf_raw, default=route["confidence"])

    # Extract structured signal
    signal = await extract_signal(msg, answer)

    # Decide whether to write memory
    should_write = (
        (route.get("memory_write") or mode in ("hub", "supervision"))
        and confidence >= CONF_MIN_WRITE
        and signal.get("pattern")
        and signal.get("importance", 0) >= 0.45
    )

    wrote_signal = False
    signal_id = None

    if should_write:
        # Dedup key prevents spamming the store with near-identical signals
        dedup_key = stable_key(
            "signal",
            mode,
            domain,
            signal.get("category") or "",
            signal.get("pattern") or ""
        )

        payload = {
            "dedupKey": dedup_key,
            "type": "chat_signal",
            "mode": mode,
            "intent": route.get("intent"),
            "domain": domain,
            "tags": list(set(tags + (signal.get("tags") or [])))[:20],
            "sessionId": session_id,
            "userId": user_id,
            "signal": signal,
            "message": msg,
            "response": trim(redact_private_bits(answer), 1200),
            "confidence": confidence,
            "modelUsed": model_used,
            "retrievedGlobalKnowledgeIds": clean_ids(global_ids),
            "retrievedChatSignalIds": clean_ids(chat_ids),
            "createdAt": now().isoformat() + "Z"
        }

        wrote_signal = await write_chat_signal(payload)
        if wrote_signal:
            signal_id = dedup_key  # local reference; your API can return a real id later

    result = {
        "response": answer,
        "confidence": confidence,
        "mode": mode,
        "intent": route.get("intent"),
        "model_used": model_used,

        "used_global_rag": bool(use_global_rag),
        "used_chat_signals": bool(use_chat_signals),

        "global_rag_cache_hit": bool(global_cache_hit),
        "chat_signals_cache_hit": bool(chat_cache_hit),

        "retrieved_global_knowledge_ids": clean_ids(global_ids),
        "retrieved_chat_signal_ids": clean_ids(chat_ids),

        "signal": signal,
        "wrote_signal": wrote_signal,
        "signal_ref": signal_id,

        "cache_hit": False
    }

    CHAT_CACHE[ckey] = {"data": result, "ts": now()}
    evict_if_needed(CHAT_CACHE)

    return result
