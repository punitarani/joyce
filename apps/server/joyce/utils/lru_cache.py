from __future__ import annotations

from collections import OrderedDict
from typing import Generic, Optional, TypeVar

V = TypeVar("V")


class LRUCache(Generic[V]):
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: OrderedDict[str, V] = OrderedDict()

    def get(self, key: str) -> Optional[V]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: V) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def remove(self, key: str) -> None:
        self.cache.pop(key)

    def __repr__(self) -> str:
        return f"{self.cache}"
