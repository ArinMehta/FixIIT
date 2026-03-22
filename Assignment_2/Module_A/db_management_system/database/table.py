
from bplustree import BPlusTree

_TYPE_MAP = {
    "int":   int,
    "float": float,
    "str":   str,
    "bool":  bool,
}


class Table:

    def __init__(self, name: str, schema: dict, order: int = 8, search_key: str = None):
        self.name       = name
        self.schema     = schema
        self.order      = order
        self.data       = BPlusTree(order=order)

        # Validate and set search key
        if search_key is None:
            search_key = next(iter(schema))           # Default to first column
        if search_key not in schema:
            raise ValueError(f"search_key '{search_key}' not found in schema")
        self.search_key = search_key

    def validate_record(self, record: dict) -> None:
        for col, type_str in self.schema.items():
            if col not in record:
                raise ValueError(f"Missing column '{col}' in record")
            expected_type = _TYPE_MAP.get(type_str, str)
            val = record[col]
            if not isinstance(val, expected_type):
                # Attempt a silent coercion; raise on failure
                try:
                    record[col] = expected_type(val)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Column '{col}': expected {type_str}, got {type(val).__name__}"
                    )
        # Warn about extra columns (non-fatal)
        extra = set(record.keys()) - set(self.schema.keys())
        if extra:
            import warnings
            warnings.warn(f"Extra columns ignored: {extra}", stacklevel=2)
    def insert(self, record: dict) -> None:
        self.validate_record(record)
        key = record[self.search_key]
        self.data.insert(key, dict(record))

    def get(self, record_id):
        return self.data.search(record_id)

    def get_all(self) -> list:
       return [v for _, v in self.data.get_all()]

    def update(self, record_id, new_record: dict) -> bool:
        self.validate_record(new_record)
        if new_record.get(self.search_key) != record_id:
            raise ValueError(
                f"new_record search_key value must match record_id "
                f"(got {new_record.get(self.search_key)!r}, expected {record_id!r})"
            )
        return self.data.update(record_id, dict(new_record))

    def delete(self, record_id) -> None:
        self.data.delete(record_id)

    def range_query(self, start_value, end_value) -> list:
        return [v for _, v in self.data.range_query(start_value, end_value)]
    
    def count(self) -> int:
        return len(self.data)

    def visualize(self, filename: str = None):
        return self.data.visualize_tree(filename)

    def __repr__(self):
        return (
            f"Table(name={self.name!r}, "
            f"schema={self.schema}, "
            f"search_key={self.search_key!r}, "
            f"records={self.count()})"
        )
