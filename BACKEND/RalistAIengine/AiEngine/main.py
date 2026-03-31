import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from Aipipeline import AIpipeline          # Solver engine (workspace)
from ChatPipeline import chat_pipeline     # Chat / Hub / Supervision engine
from Models import ProblemReq, Finalresult


# FASTAPI APP


AiEngine = FastAPI(
    title="Realist AI Engine",
    version="1.0.0",
    description="Cognitive engine for Catalyst OS"
)


# CHAT MODELS


class ChatRequest(BaseModel):
    message: str
    domain: str = "general"
    tags: List[str] = []
    sessionId: Optional[str] = None
    userId: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    confidence: Optional[float] = None
    mode: Optional[str] = None
    intent: Optional[str] = None

    model_used: Optional[str] = None

    used_global_rag: bool = False
    used_chat_signals: bool = False

    global_rag_cache_hit: bool = False
    chat_signals_cache_hit: bool = False

    retrieved_global_knowledge_ids: List[str] = []
    retrieved_chat_signal_ids: List[str] = []

    wrote_signal: bool = False
    signal_ref: Optional[str] = None

    cache_hit: bool = False


# SOLVER ENDPOINT (WORKSPACE)


@AiEngine.post("/run-pipeline", response_model=Finalresult)
async def run_pipeline(problem: ProblemReq):
    """
    High‑power problem solving engine.
    Used when a session runs AI on a problem.
    """
    return await AIpipeline(problem)


# CHAT ENDPOINTS (OS SHELL)


@AiEngine.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Team / private chat.
    Flash‑Lite → Flash escalation.
    Evolves via ChatSignals.
    """
    out = await chat_pipeline(
        req.message,
        mode="chat",
        domain=req.domain,
        tags=req.tags,
        session_id=req.sessionId,
        user_id=req.userId
    )
    return ChatResponse(**out)

@AiEngine.post("/hub", response_model=ChatResponse)
async def hub(req: ChatRequest):
    """
    Global Hub Assistant.
    Reads global knowledge only.
    No private session leakage.
    """
    out = await chat_pipeline(
        req.message,
        mode="hub",
        domain=req.domain,
        tags=req.tags,
        session_id=req.sessionId,
        user_id=req.userId
    )
    return ChatResponse(**out)

@AiEngine.post("/supervision", response_model=ChatResponse)
async def supervision(req: ChatRequest):
    """
    Cross‑session supervision.
    Detects risks, suggests improvements,
    maintains continuity.
    """
    out = await chat_pipeline(
        req.message,
        mode="supervision",
        domain=req.domain,
        tags=req.tags,
        session_id=req.sessionId,
        user_id=req.userId
    )
    return ChatResponse(**out)


# ENTRYPOINT


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:AiEngine", host="0.0.0.0", port=port)
