"""Persistence interfaces; idempotent, dialect-aware writes will be added with final schema."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def add(self, item: T) -> None:
        """Persist a validated domain object idempotently."""
        raise NotImplementedError
