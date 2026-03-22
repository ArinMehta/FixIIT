"""
bruteforce.py
-------------
A simple linear-scan "database" used as a baseline for performance comparison.
All operations run in O(n) time, making it easy to highlight the advantages of
the B+ Tree index.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


class BruteForceDB:
    """
    In-memory store backed by a plain Python list of (key, value) tuples.
    Every operation scans the entire list — no indexing whatsoever.
    """

    def __init__(self) -> None:
        self._data: List[Tuple[Any, List[Any]]] = []

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair.  Duplicate keys accumulate values."""
        for entry in self._data:
            if entry[0] == key:
                entry[1].append(value)
                return
        self._data.append((key, [value]))

    def search(self, key: Any) -> Optional[List[Any]]:
        """Linear scan; returns value list or None."""
        for entry in self._data:
            if entry[0] == key:
                return entry[1]
        return None

    def delete(self, key: Any) -> bool:
        """Remove the first entry matching `key`."""
        for i, entry in enumerate(self._data):
            if entry[0] == key:
                self._data.pop(i)
                return True
        return False

    def update(self, key: Any, new_value: Any) -> bool:
        """Replace value list for `key`."""
        for entry in self._data:
            if entry[0] == key:
                entry[1][:] = [new_value]
                return True
        return False

    def range_query(self, low: Any, high: Any) -> List[Tuple[Any, List[Any]]]:
        """Full scan filtered to [low, high]."""
        return [(k, v) for k, v in self._data if low <= k <= high]

    def get_all(self) -> List[Tuple[Any, List[Any]]]:
        return list(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"BruteForceDB(records={len(self._data)})"
