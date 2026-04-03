# chat_pipeline_fixed.py
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from models import gpt5_nano
from chat_signals import write_chat_signal
from session_graph import get_graph, find_impacts
from code_graph import get_code_graph, find_code_impacts

logger = logging.getLogger("aiengine.chat")

MODEL_TIMEOUT_FAST = 8.0


def now():
    return datetime.utcnow()


def safe_json_loads(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
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
    return {}


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


# AUTO EVOLUTION (LIGHT CHAT VERSION) 
async def auto_evolve_chat(response: str, confidence: float) -> (str, float):
    try:
        if confidence >= 0.78:
            return response, confidence

        prompt = f"""
Evaluate and improve this response.

Return JSON:
{{
 "score": 0.0,
 "improved_response": "",
 "confidence": 0.0
}}

INPUT:
{response}
"""

        raw = await safe_model_call(
            gpt5_nano,
            prompt,
            timeout=MODEL_TIMEOUT_FAST,
            retries=0
        )

        parsed = safe_json_loads(raw)
        if not parsed:
            return response, confidence

        score = float(parsed.get("score", 1.0))

        if score < 0.7:
            return (
                parsed.get("improved_response") or response,
                max(score, 0.5)
            )

        return response, confidence

    except Exception as e:
        logger.debug("Auto evolve chat skipped: %s", e)
        return response, confidence


async def chat_pipeline(
    message: str,
    *,
    mode="chat",
    domain: str = "general",
    tags: Optional[list] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    msg = (message or "")[:1400]

    # Controller (SAFE)
    try:
        ctrl_raw = await safe_model_call(
            gpt5_nano,
            msg,
            timeout=MODEL_TIMEOUT_FAST,
            retries=1
        )
        ctrl = safe_json_loads(ctrl_raw)
    except Exception as e:
        logger.warning("gpt5_nano failed in chat_pipeline: %s", e)
        ctrl = {}

    response = (
        ctrl.get("draft_response")
        or ctrl.get("response")
        or "I’m processing that. Try rephrasing if needed."
    )

    confidence = float(ctrl.get("confidence", 0.6) or 0.6)

    #  AUTO EVOLUTION 
    try:
        response, confidence = await auto_evolve_chat(response, confidence)
    except Exception as e:
        logger.debug("Auto evolution chat failed: %s", e)

    #  MEMORY WRITE
    try:
        mem = ctrl.get("memory_signal")
        if mem and isinstance(mem, dict):
            pattern = mem.get("topic")
            importance = float(mem.get("importance", 0.5) or 0.5)

            if pattern and importance >= 0.0:
                payload = {
                    "pattern": pattern,
                    "importance": importance,
                    "message": msg,
                    "response": response,
                    "sessionId": session_id,
                    "userId": user_id,
                    "createdAt": now().isoformat()
                }

                try:
                    await write_chat_signal(payload)
                except Exception as e:
                    logger.debug("write_chat_signal failed: %s", e)

    except Exception as e:
        logger.debug("Memory extraction/write failed: %s", e)

    #  SESSION IMPACT 
    if mode in ("hub", "supervision") and session_id:
        try:
            graph = await get_graph(session_id)

            try:
                entities_raw = await safe_model_call(
                    gpt5_nano,
                    f"Extract entities JSON:\n{msg}",
                    timeout=MODEL_TIMEOUT_FAST
                )
                entities = safe_json_loads(entities_raw) or []
            except Exception:
                entities = []

            impacts = find_impacts(graph, entities or [])

            if impacts:
                try:
                    insight_raw = await safe_model_call(
                        gpt5_nano,
                        f"Explain system impact:\n{json.dumps(impacts)}",
                        timeout=MODEL_TIMEOUT_FAST
                    )
                    insight = (insight_raw or "")[:300]
                    response += f"\n\n🔗 Impact:\n{insight}"
                except Exception as e:
                    logger.debug("Impact explanation failed: %s", e)

        except Exception as e:
            logger.debug("Session impact check failed: %s", e)

    # CODE IMPACT
    if mode in ("hub", "supervision") and session_id:
        try:
            code_graph = await get_code_graph(session_id)

            try:
                symbols_raw = await safe_model_call(
                    gpt5_nano,
                    f"Extract symbols JSON:\n{msg}",
                    timeout=MODEL_TIMEOUT_FAST
                )
                symbols = safe_json_loads(symbols_raw) or []
            except Exception:
                symbols = []

            code_impacts = find_code_impacts(code_graph, symbols or [])

            if code_impacts:
                try:
                    insight_raw = await safe_model_call(
                        gpt5_nano,
                        f"Explain code impact:\n{json.dumps(code_impacts)}",
                        timeout=MODEL_TIMEOUT_FAST
                    )
                    insight = (insight_raw or "")[:300]
                    response += f"\n\n🧩 Code Impact:\n{insight}"
                except Exception as e:
                    logger.debug("Code impact explanation failed: %s", e)

        except Exception as e:
            logger.debug("Code impact check failed: %s", e)

    return {
        "response": response,
        "confidence": confidence,
        "intent": ctrl.get("intent", "chat"),
        "mode": mode,
        "model_used": "gpt5_nano"
    }