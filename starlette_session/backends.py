from enum import Enum
from functools import partial
from pickle import HIGHEST_PROTOCOL, dumps, loads
from typing import Any, Optional

try:
    from redis import Redis
except ImportError:
    redis = None

from starlette_session.interfaces import ISessionBackend

_dumps = partial(dumps, protocol=HIGHEST_PROTOCOL)
_loads = partial(loads)


class BackendType(Enum):
    redis = "redis"
    cookie = "cookie"


class RedisSessionBackend(ISessionBackend):
    def __init__(self, redis):
        self.redis = redis

    def get(self, key: str) -> Optional[dict]:
        value = self.redis.get(key)
        return _loads(value) if value else None

    def set(self, key: str, value: dict, exp: Optional[int] = None) -> Optional[str]:
        return self.redis.set(key, _dumps(value), exp)

    def delete(self, key: str) -> int:
        return self.redis.delete(key)
