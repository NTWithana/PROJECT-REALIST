import os
from datetime import datetime
import httpx
from dotenv import load_dotenv
from Models import ProblemReq, Finalresult 

load_dotenv()


#  MODEL CALLS (STUBS — replace with real API calls)


# Gemini Flash — light tasks
async def flash_chat(prompt: str) -> str:
    return f"[Gemini-Flash] {prompt[:800]}"

# DeepSeek Reasoner — heavy reasoning
async def deepseek_reasoner(prompt: str) -> str:
    return f"[DeepSeek-Reasoner] {prompt[:800]}"


#  FLASH HELPERS


async def flash_clean(problem: ProblemReq) -> str:
    prompt = (
        "You are a mediator for a global human + AI hive mind.\n"
        "Clean and summarize the user's problem.\n"
        "Remove noise, repetition, and irrelevant details.\n\n"
        f"Original description:\n{problem.description}\n\n"
        "Return a concise, clear summary of the core problem."
    )
    return await flash_chat(prompt)

async def flash_detect_intent(description: str) -> str:
    prompt = (
        "You are an intent classifier.\n"
        "Choose ONE intent:\n"
        "solve, build, fix, research, analyze, plan, create, learn, explore, decide\n\n"
        f"{description}"
    )
    raw = await flash_chat(prompt)
    for intent in ["solve","build","fix","research","analyze","plan","create","learn","explore","decide"]:
        if intent in raw.lower():
            return intent
    return "solve"

async def flash_polish(text: str) -> str:
    prompt = (
        "You are polishing a final AI-generated solution.\n"
        "Improve clarity, structure, and readability.\n\n"
        f"{text}"
    )
    return await flash_chat(prompt)


#  RAG


async def retrievesimilar(problem: ProblemReq):
    BASE_URL = os.getenv("REALIST_API_URL", "http://localhost:5109")
    url = f"{BASE_URL}/api/knowledge/semantic-similar"

    query_text = problem.description or problem.suggestions or ""

    params = {"query": query_text}

    if getattr(problem, "domain", None):
        params["domain"] = problem.domain

    if problem.tags:
        params["tags"] = problem.tags

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

        if response.status_code != 200:
            return ""

        data = response.json()
        blocks = []

        for item in data:
            blocks.append(
                f"- Problem: {item.get('problem_summary')}\n"
                f"  Solution: {item.get('solution_summary')}\n"
                f"  Meta: confidence={item.get('confidence')}, "
                f"approved={item.get('approved_count')}, "
                f"optimized={item.get('optimized_count')}, "
                f"reused={item.get('reused_count')}"
            )

        return "\n".join(blocks)


#  LOGGING


def logstep(iteration: int, model: str, output: str, confidence: float, rationale: str) -> dict:
    return {
        "iteration": iteration,
        "model": model,
        "output": output,
        "confidence": confidence,
        "rationale": rationale,
    }


#  MODEL ROUTER


async def model_router(task: str, context: str = "") -> str:
    if task == "reason":
        return await deepseek_reasoner(context)

    if task == "polish":
        return await flash_polish(context)

    raise ValueError(f"Unknown task: {task}")


#  SELF-CRITIQUE & IMPROVEMENTS


async def self_critique(solution: str) -> str:
    prompt = (
        "Critically evaluate the solution.\n"
        "List weaknesses, risks, and missing elements.\n\n"
        f"{solution}"
    )
    return await deepseek_reasoner(prompt)

async def improvement_suggestions(solution: str) -> str:
    prompt = (
        "Suggest concrete improvements.\n\n"
        f"{solution}"
    )
    return await deepseek_reasoner(prompt)


#  PIPELINE


async def hive_pipeline(problem: ProblemReq, intent: str):
    history = []
    iteration = 1
    confidence = 0.6

    # Step 1 — Clean
    cleaned = await flash_clean(problem)
    history.append(logstep(iteration, "Flash Clean", cleaned, confidence, "Cleaned input"))
    iteration += 1
    confidence += 0.1

    # Step 2 — RAG
    retrieved = await retrievesimilar(problem)
    history.append(logstep(iteration, "RAG", retrieved or "None", confidence, "Retrieved context"))
    iteration += 1
    confidence += 0.05

    # Step 3 — Reason
    reason_prompt = f"""
Intent: {intent}

Problem:
{cleaned}

Context:
{retrieved}
"""
    core_solution = await model_router("reason", reason_prompt)
    history.append(logstep(iteration, "Reasoner", core_solution, confidence, "Generated solution"))
    iteration += 1
    confidence += 0.1

    # Step 4 — Critique
    critique = await self_critique(core_solution)
    history.append(logstep(iteration, "Critique", critique, confidence, "Evaluated solution"))
    iteration += 1
    confidence += 0.05

    # Step 5 — Improvements
    improvements = await improvement_suggestions(core_solution)
    history.append(logstep(iteration, "Improvements", improvements, confidence, "Suggested improvements"))
    iteration += 1
    confidence += 0.05

    #  Step 6 — FINAL SYNTHESIS + POLISH (UPGRADED)
    final_input = f"""
You are producing the final answer for a global AI system.

CORE SOLUTION:
{core_solution}

CRITIQUE:
{critique}

IMPROVEMENTS:
{improvements}

Instructions:
- Fix weaknesses
- Apply improvements
- Keep good parts
- Output a complete, structured answer
"""

    final = await model_router("polish", final_input)

    history.append(logstep(
        iteration,
        "Final Synthesis",
        final,
        confidence,
        "Synthesized improved final output"
    ))

    return final, history, iteration, confidence


#  MAIN ENTRY


async def AIpipeline(problem: ProblemReq) -> Finalresult:
    description = (problem.description or "").lower()

    intent = await flash_detect_intent(description)

    final, history, iteration, confidence = await hive_pipeline(problem, intent)

    return Finalresult(
        Status="ok",
        OptimisedSolution=final,
        Confidence=confidence,
        Rationale=history[-1]["rationale"],
        Iteration=iteration,
        Created_At=datetime.utcnow()
    )