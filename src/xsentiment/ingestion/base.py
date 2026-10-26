"""Replaceable adapter interface adapted from GraphOne's source-adapter pattern."""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Generic, TypeVar

from xsentiment.ingestion.contracts import DiscoveredItem, SourceRecord
from xsentiment.ingestion.http import AsyncHttpClient

T = TypeVar("T", bound=SourceRecord)


class SourceAdapter(ABC, Generic[T]):
    """A provider adapter separates discovery, fetching and parsing."""

    name: str

    def __init__(self, http_client: AsyncHttpClient) -> None:
        self.http_client = http_client

    @abstractmethod
    async def discover(self) -> AsyncIterator[DiscoveredItem]:
        """Yield only source items actually reported by the provider."""
        raise NotImplementedError

    @abstractmethod
    async def fetch(self, item: DiscoveredItem) -> str:
        """Fetch a discovered item using the shared HTTP client."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, item: DiscoveredItem, body: str) -> T:
        """Parse the response without inventing missing values."""
        raise NotImplementedError
