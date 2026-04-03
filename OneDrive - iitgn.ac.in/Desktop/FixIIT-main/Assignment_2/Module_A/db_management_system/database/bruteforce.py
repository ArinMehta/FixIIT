"""
BruteForceDB — a naive list-based database used as a performance baseline.
All operations are O(n) (linear scan), making it ideal for benchmarking
against the O(log n) B+ Tree.
"""


class BruteForceDB:
    def __init__(self):
        # Internal storage: list of [key, value] pairs (unsorted)
        self._store: list = []

    def insert(self, key, value) -> None:
        """
        Insert (key, value).  If the key already exists, update in-place.
        Time complexity: O(n)
        """
        for item in self._store:
            if item[0] == key:
                item[1] = value
                return
        self._store.append([key, value])

    def search(self, key):
        """
        Return the value for `key`, or None if not found.
        Time complexity: O(n)
        """
        for k, v in self._store:
            if k == key:
                return v
        return None

    def delete(self, key) -> bool:
        """
        Remove the entry with `key`.
        Returns True if found and deleted, False otherwise.
        Time complexity: O(n)
        """
        for i, (k, v) in enumerate(self._store):
            if k == key:
                self._store.pop(i)
                return True
        return False

    def update(self, key, new_value) -> bool:
        """
        Update value for `key`.
        Returns True on success, False if key not found.
        Time complexity: O(n)
        """
        for item in self._store:
            if item[0] == key:
                item[1] = new_value
                return True
        return False

    def range_query(self, start_key, end_key) -> list:
        """
        Return all (key, value) pairs where start_key <= key <= end_key,
        sorted by key.
        Time complexity: O(n log n)  (linear scan + sort)
        """
        results = [(k, v) for k, v in self._store if start_key <= k <= end_key]
        return sorted(results, key=lambda x: x[0])

    def get_all(self) -> list:
        """
        Return all (key, value) pairs sorted by key.
        Time complexity: O(n log n)
        """
        return sorted(self._store, key=lambda x: x[0])

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key) -> bool:
        return self.search(key) is not None

    def __repr__(self):
        return f"BruteForceDB(size={len(self)})"
