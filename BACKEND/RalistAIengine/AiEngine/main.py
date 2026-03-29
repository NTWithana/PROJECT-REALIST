import os
import uvicorn
from fastapi import FastAPI
from Aipipeline import AIpipeline
from Models import ProblemReq, Finalresult
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

AiEngine = FastAPI(
    title="Realist AI Engine",
    version="1.0.0",
    description="AI pipeline for Realist backend"
)

@AiEngine.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Simple bridge: treat chat as a problem with just description
    result = await AIpipeline(ProblemReq(
        description=req.message,
        suggestions="",
        domain="general",
        tags=[],
        sessionId=None,
        intent=None,
    ))
    return ChatResponse(response=result.OptimisedSolution or "No response")

@AiEngine.post("/run-pipeline", response_model=Finalresult)
async def run_pipeline(problem: ProblemReq):

    # 1. Receive problem description

    return await AIpipeline(problem)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:AiEngine", host="0.0.0.0", port=port)
