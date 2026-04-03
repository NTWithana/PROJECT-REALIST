import json
from redis_cache import redis_get_json, redis_set_json

CODE_GRAPH_KEY = "code_graph"

async def get_code_graph(session_id: str):
    key = f"{CODE_GRAPH_KEY}:{session_id}"
    return await redis_get_json(key) or {}

async def save_code_graph(session_id: str, graph: dict):
    key = f"{CODE_GRAPH_KEY}:{session_id}"
    await redis_set_json(key, graph, 86400)

async def update_code_graph(session_id: str, file_data: dict):
    graph = await get_code_graph(session_id)

    file_path = file_data.get("file")
    if not file_path:
        return

    graph[file_path] = file_data
    await save_code_graph(session_id, graph)

def find_code_impacts(graph: dict, changed_symbols: list):
    impacts = []

    for file, data in graph.items():
        for dep in data.get("depends_on", []):
            if dep in changed_symbols:
                impacts.append({
                    "file": file,
                    "reason": f"Depends on {dep}"
                })

    return impacts 