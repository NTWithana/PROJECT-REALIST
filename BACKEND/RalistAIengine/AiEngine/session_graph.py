
import json
from typing import Dict, List, Any
from redis_cache import redis_get_json, redis_set_json
SESSION_GRAPH_KEY = "session_graph"
#  GET GRAPH 
async def get_graph(session_id: str) -> Dict:
    key = f"{SESSION_GRAPH_KEY}:{session_id}"
    graph = await redis_get_json(key)
    return graph or {"entities": {}, "dependencies": []}
# SAVE GRAPH
async def save_graph(session_id: str, graph: Dict):
    key = f"{SESSION_GRAPH_KEY}:{session_id}"
    await redis_set_json(key, graph, ttl_seconds=86400)
# ADD SIGNA
async def update_graph(session_id: str, signal: Dict):
    graph = await get_graph(session_id)
    for ent in signal.get("entities", []):
        graph["entities"][ent] = {
            "last_updated": signal.get("timestamp"),
            "changes": signal.get("actions", [])
        }
    for dep in signal.get("dependencies", []):
        if dep not in graph["dependencies"]:
            graph["dependencies"].append(dep)
    await save_graph(session_id, graph)
#FIND IMPACT 
def find_impacts(graph: Dict, changed_entities: List[str]) -> List[Dict]:
    impacts = []
    for dep in graph.get("dependencies", []):
        if dep.get("to") in changed_entities:
            impacts.append({
                "affected": dep.get("from"),
                "source": dep.get("to")
            })
    return impacts
