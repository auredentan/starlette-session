from abc import ABC, abstractmethod
from typing import Any, Optional


class ISessionBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    async def set(self, key: str, value: dict, exp: Optional[int]) -> Optional[str]:
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    async def delete(self, key: str) -> Any:
        raise NotImplementedError()  # pragma: no cover
