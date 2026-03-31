import os
import json
import hashlib
from datetime import timedelta
from typing import Any, Optional

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "").strip()

def _hash_key(key: str) -> str:
    return hashlib.md5(key.encode("utf-8")).hexdigest()

class RedisCache:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        if not REDIS_URL:
            self._client = None
            return
        self._client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    def enabled(self) -> bool:
        return self._client is not None

    async def get_json(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        v = await self._client.get(_hash_key(key))
        if not v:
            return None
        try:
            return json.loads(v)
        except:
            return None

    async def set_json(self, key: str, value: Any, ttl: timedelta):
        if not self._client:
            return
        await self._client.setex(_hash_key(key), int(ttl.total_seconds()), json.dumps(value))

    async def close(self):
        if self._client:
            await self._client.close()
