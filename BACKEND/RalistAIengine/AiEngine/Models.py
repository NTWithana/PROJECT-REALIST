import os
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import os
import json
import asyncio
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ---------- CLIENTS ----------
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

deepseek_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ---------- SAFE PARSE ----------
def safe_text(resp):
    try:
        return resp.output_text
    except:
        try:
            return resp.output[0].content[0].text
        except:
            return '{"error":"invalid_response"}'

# ---------- GPT-5 NANO ----------
async def gpt5_nano(prompt: str, timeout: float = 8.0) -> str:
    try:
        resp = await openai_client.responses.create(
            model="gpt-5-nano",
            input=prompt,
            timeout=timeout
        )
        return safe_text(resp)
    except Exception as e:
        return '{"error":"nano_failed"}'

# ---------- DEEPSEEK V3.2 SPECIAL ----------
async def deepseek_reasoner(prompt: str, timeout: float = 18.0) -> str:
    try:
        try:
            resp = await deepseek_client.responses.create(
                model="deepseek-v3.2-speciale",
                input=prompt,
                timeout=timeout
            )
            return safe_text(resp)
        except:
            # fallback
            resp = await deepseek_client.responses.create(
                model="deepseek-reasoner",
                input=prompt,
                timeout=timeout
            )
            return safe_text(resp)

    except Exception:
        return '{"error":"deep_failed"}'
# REQUEST MODEL
class ProblemReq(BaseModel):
    description: str
    suggestions: str
    domain: Optional[str] = "general"
    tags: Optional[List[str]] = []
    sessionId: Optional[str] = None
    intent: Optional[str] = None
# RESPONSE MODEL 
class Finalresult(BaseModel):
    Status: str = "ok"
    OptimisedSolution: Optional[str] = None
    Critique: Optional[str] = None
    Improvements: Optional[str] = None
    Confidence: Optional[float] = None
    Rationale: Optional[str] = None
    Iteration: int = Field(default=1)
    Created_At: datetime = Field(default_factory=datetime.utcnow)
    # Hybrid artifacts
    DeepCore: Optional[str] = None
    UsedRag: bool = False
    UsedDeep: bool = False
    DeepCacheHit: bool = False
    RagCacheHit: bool = False
    ProblemKey: Optional[str] = None
    RetrievedKnowledgeIds: List[str] = Field(default_factory=list)

