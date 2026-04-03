
import os
import json
import hashlib
from typing import Any, Optional
import redis.asyncio as redis
REDIS_URL = os.getenv("REDIS_URL", "").strip()
def _hash_key(key: str) -> str:
    return hashlib.md5(key.encode("utf-8")).hexdigest()
class RedisCache:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    async def connect(self):
        if not REDIS_URL:
            return
        self.client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    def enabled(self) -> bool:
        return self.client is not None
    async def get_json(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        raw = await self.client.get(_hash_key(key))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except:
            return None
    async def set_json(self, key: str, value: Any, ttl_seconds: int):
        if not self.client:
            return
        await self.client.setex(_hash_key(key), ttl_seconds, json.dumps(value))

_cache = RedisCache()

async def redis_get_json(key: str):
    return await _cache.get_json(key)

async def redis_set_json(key: str, value, ttl_seconds: int):
    await _cache.set_json(key, value, ttl_seconds)