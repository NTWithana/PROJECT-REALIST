import os
import time
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr
from Aipipeline import AIpipeline
from ChatPipeline import chat_pipeline
from Models import ProblemReq, Finalresult
from redis_cache import RedisCache
AiEngine = FastAPI(
    title="Realist AI Engine",
    version="1.0.0",
    description="Cognitive engine for Catalyst OS"
)
# CORS (LOCKED DOWN)
allowed_origins = [
    "https://project-realist-frontend.onrender.com",
    "https://project-realist.onrender.com"
]
AiEngine.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
# RATE LIMITING
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "120"))
_window = {}
@AiEngine.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now_min = int(time.time() // 60)
    win, count = _window.get(ip, (now_min, 0))
    if win != now_min:
        win, count = now_min, 0
    count += 1
    _window[ip] = (win, count)
    if count > RATE_LIMIT_RPM:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    start = time.time()
    resp = await call_next(request)
    resp.headers["X-Request-Time-ms"] = str(int((time.time() - start) * 1000))
    return resp
# REDIS CACHE
cache = RedisCache()
@AiEngine.on_event("startup")
async def _startup():
    await cache.connect()
@AiEngine.on_event("shutdown")
async def _shutdown():
    if cache.client:
        await cache.client.close()
# MODELS
class ChatRequest(BaseModel):
    message: constr(min_length=1, max_length=2000)
    domain: str = "general"
    tags: List[str] = Field(default_factory=list)
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
# SOLVER ENDPOINT
@AiEngine.post("/run-pipeline", response_model=Finalresult)
async def run_pipeline(problem: ProblemReq):
    return await AIpipeline(problem)
# CHAT ENDPOINTS
@AiEngine.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    out = await chat_pipeline(
        req.message,
        mode="chat",
        domain=req.domain,
        tags=req.tags,
        session_id=req.sessionId,
        user_id=req.userId,
    )
    return ChatResponse(**out)
@AiEngine.post("/hub", response_model=ChatResponse)
async def hub(req: ChatRequest):
    out = await chat_pipeline(
        req.message,
        mode="hub",
        domain=req.domain,
        tags=req.tags,
        session_id=req.sessionId,
        user_id=req.userId,
    )
    return ChatResponse(**out)
@AiEngine.post("/supervision", response_model=ChatResponse)
async def supervision(req: ChatRequest):
    out = await chat_pipeline(
        req.message,
        mode="supervision",
        domain=req.domain,
        tags=req.tags,
        session_id=req.sessionId,
        user_id=req.userId,
    )
    return ChatResponse(**out)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:AiEngine", host="0.0.0.0", port=port)
