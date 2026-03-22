"""
table.py
--------
Relational-style table built on top of BPlusTree.
Supports:
  - Schema definition  (column names + data types)
  - INSERT / GET / UPDATE / DELETE operations
  - Range queries on the search key
  - Aggregate functions: COUNT, SUM, MIN, MAX, AVG
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from .bplustree import BPlusTree


class Table:
    """
    A named table with a fixed schema backed by a B+ Tree index on the search key.

    Parameters
    ----------
    name       : table name (string)
    schema     : dict of {column_name: data_type}, e.g. {"id": int, "name": str}
    order      : B+ Tree order — max number of children per internal node (default 8)
    search_key : column name used as the B+ Tree key (must be in schema)
    """

    def __init__(
        self,
        name: str,
        schema: Dict[str, type],
        order: int = 8,
        search_key: str = None,
    ) -> None:
        if search_key and search_key not in schema:
            raise ValueError(f"search_key '{search_key}' must be in schema.")
        self.name = name
        self.schema = schema
        self.order = order
        self.data = BPlusTree(order=order)   # accessed as table.data per template
        self.search_key = search_key

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_record(self, record: Dict[str, Any]) -> None:
        """
        Validate that the record matches the schema:
        - All required columns are present
        - Data types are correct
        """
        for col, dtype in self.schema.items():
            if col not in record:
                raise ValueError(f"Record missing column '{col}'.")
            if not isinstance(record[col], dtype):
                raise TypeError(
                    f"Column '{col}' expects {dtype.__name__}, "
                    f"got {type(record[col]).__name__}."
                )

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def insert(self, record: Dict[str, Any]) -> None:
        """
        Insert a new record into the table.
        The key used for insertion is the value of the search_key field.
        """
        self.validate_record(record)
        key = record[self.search_key]
        self.data.insert(key, record)

    def get(self, record_id: Any) -> Optional[List[Any]]:
        """
        Retrieve a single record by its ID (i.e., the value of search_key).
        Returns the value list stored under that key, or None if not found.
        """
        return self.data.search(record_id)

    def get_all(self) -> List[Tuple[Any, Any]]:
        """
        Retrieve all records stored in the table in sorted order by search key.
        Returns list of (key, value_list) tuples.
        """
        return self.data.get_all()

    def update(self, record_id: Any, new_record: Dict[str, Any]) -> bool:
        """
        Update a record identified by record_id with new_record data.
        Validates new_record against schema before updating.
        Returns True if successful, False if key not found.
        """
        self.validate_record(new_record)
        return self.data.update(record_id, new_record)

    def delete(self, record_id: Any) -> bool:
        """
        Delete the record from the table by its record_id.
        Returns True if deleted, False if not found.
        """
        return self.data.delete(record_id)

    def range_query(self, start_value: Any, end_value: Any) -> List[Tuple[Any, Any]]:
        """
        Perform a range query using the search key.
        Returns all (key, value_list) pairs where start_value <= key <= end_value.
        """
        return self.data.range_query(start_value, end_value)

    # ------------------------------------------------------------------
    # Aggregations (additional utility beyond template)
    # ------------------------------------------------------------------

    def count(self, where: Optional[Dict[str, Any]] = None) -> int:
        """Count records, optionally filtered by where dict."""
        rows = self._all_records()
        if where:
            rows = [r for r in rows if self._matches(r, where)]
        return len(rows)

    def sum(self, column: str, where: Optional[Dict[str, Any]] = None) -> float:
        rows = self._all_records()
        if where:
            rows = [r for r in rows if self._matches(r, where)]
        return sum(r[column] for r in rows if r.get(column) is not None)

    def avg(self, column: str, where: Optional[Dict[str, Any]] = None) -> float:
        rows = self._all_records()
        if where:
            rows = [r for r in rows if self._matches(r, where)]
        vals = [r[column] for r in rows if r.get(column) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    def min(self, column: str, where: Optional[Dict[str, Any]] = None) -> Any:
        rows = self._all_records()
        if where:
            rows = [r for r in rows if self._matches(r, where)]
        vals = [r[column] for r in rows if r.get(column) is not None]
        return min(vals) if vals else None

    def max(self, column: str, where: Optional[Dict[str, Any]] = None) -> Any:
        rows = self._all_records()
        if where:
            rows = [r for r in rows if self._matches(r, where)]
        vals = [r[column] for r in rows if r.get(column) is not None]
        return max(vals) if vals else None

    # ------------------------------------------------------------------
    # Select helper (used by notebook for WHERE queries)
    # ------------------------------------------------------------------

    def select(
        self,
        where: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return rows matching all conditions in where dict (AND semantics).
        If where is None, return all rows.
        columns restricts which fields are returned.
        """
        rows = self._all_records()
        if where:
            rows = [r for r in rows if self._matches(r, where)]
        if columns:
            rows = [{c: r[c] for c in columns if c in r} for r in rows]
        return rows

    def select_range(self, low: Any, high: Any) -> List[Dict[str, Any]]:
        """Range query returning flat list of record dicts."""
        pairs = self.data.range_query(low, high)
        return [record for _, value_list in pairs for record in value_list]

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    def _all_records(self) -> List[Dict[str, Any]]:
        """Flatten all (key, value_list) pairs into a list of record dicts."""
        pairs = self.data.get_all()
        return [record for _, value_list in pairs for record in value_list]

    @staticmethod
    def _matches(record: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        return all(record.get(k) == v for k, v in conditions.items())

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    def visualize(self, filename: Optional[str] = None):
        """Render the underlying B+ Tree. Returns Graphviz Digraph object."""
        fname = filename or f"tree_{self.name}"
        return self.data.visualize_tree(fname)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return sum(len(vl) for _, vl in self.data.get_all())

    def __repr__(self) -> str:
        return (
            f"Table(name={self.name!r}, search_key={self.search_key!r}, "
            f"rows={len(self)})"
        )