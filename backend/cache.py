from collections import OrderedDict
from typing import Dict, Any, Optional
import time


class QueryCache:
    """
    High-Performance In-Memory Query Cache with Least Recently Used (LRU) Eviction.
    
    PURPOSE:
    Provides sub-millisecond (O(1)) response times for high-frequency or repeated
    queries (e.g. standard shift start checks, repeated alarm code lookups).
    
    DATA STRUCTURE:
    - collections.OrderedDict: Implements a Doubly Linked List + Hash Map hybrid.
      - Hash Map: Provides O(1) key-to-node lookup.
      - Doubly Linked List: Tracks recency in O(1) time without list shifts.
    """

    def __init__(self, capacity: int = 128, ttl_seconds: int = 3600):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        # OrderedDict stores: normalized_query -> {"response": data, "timestamp": time.time()}
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached response in O(1) average time.
        Evicts expired records automatically.
        """
        clean_key = key.strip().lower()
        if clean_key not in self._cache:
            return None

        entry = self._cache[clean_key]
        now = time.time()

        # TTL check
        if now - entry["timestamp"] > self.ttl_seconds:
            del self._cache[clean_key]
            return None

        # Move to end to mark as most recently used (O(1))
        self._cache.move_to_end(clean_key)
        return entry["response"]

    def put(self, key: str, value: Dict[str, Any]):
        """
        Stores response in O(1) time. Evicts least recently used item if capacity exceeded.
        """
        clean_key = key.strip().lower()
        if clean_key in self._cache:
            self._cache.move_to_end(clean_key)
        else:
            if len(self._cache) >= self.capacity:
                # Evict the least recently used item (first element in FIFO order)
                self._cache.popitem(last=False)

        self._cache[clean_key] = {
            "response": value,
            "timestamp": time.time()
        }

    def clear(self):
        self._cache.clear()

    def size(self) -> int:
        return len(self._cache)
