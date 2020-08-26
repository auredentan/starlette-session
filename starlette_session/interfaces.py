from abc import ABC, abstractmethod
from typing import Any, Optional


class ISessionBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[dict]:
        raise NotImplementedError()

    @abstractmethod
    def set(self, key: str, value: dict, exp_in_mins: str) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def delete(key: str) -> int:
        raise NotImplementedError()
