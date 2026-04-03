import asyncio
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import os
import json
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

assert OPENAI_API_KEY, "Missing OPENAI_API_KEY"
assert DEEPSEEK_API_KEY, "Missing DEEPSEEK_API_KEY"

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
deepseek_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

def extract_text(resp):
    try:
        return resp.output[0].content[0].text
    except Exception:
        return json.dumps({"error": "invalid_response"})

async def gpt5_nano(prompt: str, timeout: float = 8.0) -> str:
    resp = await openai_client.responses.create(
        model="gpt-5-nano",
        input=prompt,
        timeout=timeout
    )
    return extract_text(resp)

async def deepseek_reasoner(prompt: str, timeout: float = 18.0) -> str:
    try:
        resp = await deepseek_client.responses.create(
            model="deepseek-v3.2-speciale",
            input=prompt,
            timeout=timeout
        )
    except Exception:
        resp = await deepseek_client.responses.create(
            model="deepseek-reasoner",
            input=prompt,
            timeout=timeout
        )
    return extract_text(resp)

# MODELS
class ProblemReq(BaseModel):
    description: str
    suggestions: Optional[str] = ""
    domain: Optional[str] = "general"
    tags: Optional[List[str]] = []
    sessionId: Optional[str] = None
    intent: Optional[str] = None

class Finalresult(BaseModel):
    Status: str = "ok"
    OptimisedSolution: Optional[str] = None
    Critique: Optional[str] = None
    Improvements: Optional[str] = None
    Confidence: Optional[float] = None
    Rationale: Optional[str] = None
    Iteration: int = Field(default=1)
    Created_At: datetime = Field(default_factory=datetime.utcnow)

    DeepCore: Optional[str] = None
    UsedRag: bool = False
    UsedDeep: bool = False
    DeepCacheHit: bool = False
    RagCacheHit: bool = False
    ProblemKey: Optional[str] = None
    RetrievedKnowledgeIds: List[str] = Field(default_factory=list)