from fastapi import FastAPI
from Aipipeline import AIpipeline
from Models import ProblemReq, Finalresult

AiEngine = FastAPI(
    title="Realist AI Engine",
    version="1.0.0",
    description="AI pipeline for Realist backend"
)

@AiEngine.post("/run-pipeline", response_model=Finalresult)
async def run_pipeline(problem: ProblemReq):

    # 1. Receive problem description

    return await AIpipeline(problem)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:AiEngine", host="0.0.0.0", port=8000)
