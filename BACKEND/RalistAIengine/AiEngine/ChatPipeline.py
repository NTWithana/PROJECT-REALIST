import json
from datetime import datetime

from models import gpt5_nano
from chat_signals import write_chat_signal
from session_graph import get_graph, find_impacts
from code_graph import get_code_graph, find_code_impacts

MODEL_TIMEOUT_FAST = 8.0

def now():
    return datetime.utcnow()

def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except:
        return {}

async def chat_pipeline(message: str, *, mode="chat", session_id=None, user_id=None):

    msg = (message or "")[:1400]

    ctrl = safe_json_loads(await gpt5_nano(msg, MODEL_TIMEOUT_FAST))

    response = ctrl.get("draft_response") or "Thinking..."

    # MEMORY
    if ctrl.get("memory_signal"):
        await write_chat_signal({
            "pattern": ctrl["memory_signal"].get("topic"),
            "importance": ctrl["memory_signal"].get("importance"),
            "message": msg,
            "response": response,
            "sessionId": session_id,
            "userId": user_id,
            "createdAt": now().isoformat()
        })

    # SESSION IMPACT
    if mode in ("hub", "supervision") and session_id:
        try:
            graph = await get_graph(session_id)
            entities = safe_json_loads(
                await gpt5_nano(f"Extract entities JSON:\n{msg}")
            ) or []

            impacts = find_impacts(graph, entities)

            if impacts:
                insight = await gpt5_nano(
                    f"Explain system impact:\n{json.dumps(impacts)}"
                )
                response += f"\n\n🔗 Impact:\n{insight[:300]}"
        except:
            pass

    # CODE IMPACT
    if mode in ("hub", "supervision") and session_id:
        try:
            code_graph = await get_code_graph(session_id)

            symbols = safe_json_loads(
                await gpt5_nano(f"Extract symbols JSON:\n{msg}")
            ) or []

            code_impacts = find_code_impacts(code_graph, symbols)

            if code_impacts:
                insight = await gpt5_nano(
                    f"Explain code impact:\n{json.dumps(code_impacts)}"
                )
                response += f"\n\n🧩 Code Impact:\n{insight[:300]}"
        except:
            pass

    return {
        "response": response,
        "confidence": ctrl.get("confidence", 0.6),
        "intent": ctrl.get("intent", "chat"),
        "mode": mode,
        "model_used": "gpt5_nano"
    }