# SAP Datasphere MCP Server
# File: cache.py
# Version: v1

"""Small in-process TTL cache used for metadata-heavy calls (v0.3+).

Design goals:
- Simple (no external deps).
- Safe defaults.
- Diagnostics-friendly (hits/misses/size/evictions).
- TTL + max entries are configurable via DatasphereConfig (env-driven).
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Hashable, Optional, Tuple


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    expirations: int = 0


class TTLCache:
    """A tiny TTL + LRU-ish cache.

    - TTL is enforced per-entry.
    - When max_entries is exceeded, we evict oldest entries (LRU-ish).
    - Intended for small metadata payloads.
    """

    def __init__(self, ttl_seconds: int = 60, max_entries: int = 128) -> None:
        self.ttl_seconds = int(ttl_seconds)
        self.max_entries = int(max_entries)
        self._store: "OrderedDict[Hashable, Tuple[float, Any]]" = OrderedDict()
        self._stats = CacheStats()

    @property
    def enabled(self) -> bool:
        return self.ttl_seconds > 0 and self.max_entries > 0

    def get(self, key: Hashable) -> Optional[Any]:
        """Return cached value if present and not expired, else None."""
        if not self.enabled:
            self._stats.misses += 1
            return None

        now = time.time()
        entry = self._store.get(key)
        if entry is None:
            self._stats.misses += 1
            return None

        expires_at, value = entry
        if expires_at < now:
            self._stats.misses += 1
            self._stats.expirations += 1
            self._store.pop(key, None)
            return None

        # refresh LRU-ish order
        self._store.move_to_end(key)
        self._stats.hits += 1
        return value

    def set(self, key: Hashable, value: Any) -> None:
        """Insert/update cached value."""
        if not self.enabled:
            return

        expires_at = time.time() + float(self.ttl_seconds)

        if key in self._store:
            self._store.move_to_end(key)

        self._store[key] = (expires_at, value)
        self._stats.sets += 1
        self._evict_if_needed()

    def _evict_if_needed(self) -> None:
        if not self.enabled:
            return

        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)
            self._stats.evictions += 1

    def purge_expired(self) -> int:
        """Remove expired entries and return count removed."""
        if not self.enabled or not self._store:
            return 0

        now = time.time()
        keys_to_delete = [k for k, (exp, _) in self._store.items() if exp < now]
        for k in keys_to_delete:
            self._store.pop(k, None)

        if keys_to_delete:
            self._stats.expirations += len(keys_to_delete)

        return len(keys_to_delete)

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "ttl_seconds": self.ttl_seconds,
            "max_entries": self.max_entries,
            "size": len(self._store),
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "sets": self._stats.sets,
            "evictions": self._stats.evictions,
            "expirations": self._stats.expirations,
        }
