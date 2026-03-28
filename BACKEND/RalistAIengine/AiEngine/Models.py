from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Incoming request from RealistAPI
class ProblemReq(BaseModel):
    description: str
    suggestions: str
    domain: Optional[str] = "general"
    tags: Optional[List[str]] = []
    sessionId: Optional[str] = None
    intent: Optional[str] = None

# Outgoing response to RealistAPI
class Finalresult(BaseModel):
    Status: str = "ok"
    OptimisedSolution: Optional[str] = None
    Critique: Optional[str] = None
    Improvements: Optional[str] = None
    Confidence: Optional[float] = None
    Rationale: Optional[str] = None
    Iteration: int = Field(default=1)
    Created_At: datetime = Field(default_factory=datetime.utcnow)