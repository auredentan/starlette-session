from enum import Enum
from functools import partial
from pickle import HIGHEST_PROTOCOL, dumps, loads
from typing import Any, Optional

try:
    from redis import Redis
except ImportError:
    Redis = None

try:
    from aioredis import Redis as AioRedis
except ImportError:
    AioRedis = None


from starlette_session.interfaces import ISessionBackend

_dumps = partial(dumps, protocol=HIGHEST_PROTOCOL)
_loads = partial(loads)


class BackendType(Enum):
    redis = "redis"
    aioRedis = "aioRedis"
    cookie = "cookie"


class RedisSessionBackend(ISessionBackend):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[dict]:
        value = self.redis.get(key)
        return _loads(value) if value else None

    async def set(
        self, key: str, value: dict, exp: Optional[int] = None
    ) -> Optional[str]:
        return self.redis.set(key, _dumps(value), exp)

    async def delete(self, key: str) -> int:
        return self.redis.delete(key)


class AioRedisSessionBackend(ISessionBackend):
    def __init__(self, redis: AioRedis):
        self.redis = redis

    async def get(self, key: str) -> Optional[dict]:
        value = await self.redis.get(key)
        return _loads(value) if value else None

    async def set(
        self, key: str, value: dict, exp: Optional[int] = None
    ) -> Optional[str]:
        return await self.redis.set(key, _dumps(value), expire=exp)

    async def delete(self, key: str) -> int:
        return await self.redis.delete(key)
