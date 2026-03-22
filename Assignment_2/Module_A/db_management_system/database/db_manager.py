from table import Table


class DatabaseManager:
    """
    Manages multiple databases, each containing zero or more tables.
    """

    def __init__(self):
        self.databases: dict[str, dict[str, Table]] = {}

    def create_database(self, db_name: str) -> None:
        if db_name in self.databases:
            raise ValueError(f"Database '{db_name}' already exists.")
        self.databases[db_name] = {}
        print(f"[OK] Database '{db_name}' created.")

    def delete_database(self, db_name: str) -> None:
        self._require_db(db_name)
        del self.databases[db_name]
        print(f"[OK] Database '{db_name}' deleted.")

    def list_databases(self) -> list:
        return sorted(self.databases.keys())

    def create_table(
        self,
        db_name: str,
        table_name: str,
        schema: dict,
        order: int = 8,
        search_key: str = None,
    ) -> Table:
        self._require_db(db_name)
        if table_name in self.databases[db_name]:
            raise ValueError(
                f"Table '{table_name}' already exists in database '{db_name}'."
            )
        table = Table(name=table_name, schema=schema, order=order, search_key=search_key)
        self.databases[db_name][table_name] = table
        print(f"[OK] Table '{table_name}' created in '{db_name}' "
              f"(order={order}, search_key={table.search_key!r}).")
        return table

    def delete_table(self, db_name: str, table_name: str) -> None:
        self._require_table(db_name, table_name)
        del self.databases[db_name][table_name]
        print(f"[OK] Table '{table_name}' deleted from '{db_name}'.")

    def list_tables(self, db_name: str) -> list:
        self._require_db(db_name)
        return sorted(self.databases[db_name].keys())

    def get_table(self, db_name: str, table_name: str) -> Table:
        self._require_table(db_name, table_name)
        return self.databases[db_name][table_name]

    def insert(self, db_name: str, table_name: str, record: dict) -> None:
        self.get_table(db_name, table_name).insert(record)

    def get(self, db_name: str, table_name: str, record_id):
        return self.get_table(db_name, table_name).get(record_id)

    def update(self, db_name: str, table_name: str, record_id, new_record: dict) -> bool:
        return self.get_table(db_name, table_name).update(record_id, new_record)

    def delete(self, db_name: str, table_name: str, record_id) -> None:
        self.get_table(db_name, table_name).delete(record_id)

    def range_query(self, db_name: str, table_name: str, start, end) -> list:
        return self.get_table(db_name, table_name).range_query(start, end)

    def get_all(self, db_name: str, table_name: str) -> list:
        return self.get_table(db_name, table_name).get_all()

    def describe(self, db_name: str = None) -> None:
        if db_name is None:
            print(f"DatabaseManager — {len(self.databases)} database(s)")
            for name in self.list_databases():
                tables = self.databases[name]
                print(f"  └─ {name}  ({len(tables)} table(s))")
                for tname, tbl in tables.items():
                    print(f"       └─ {tname}  rows={tbl.count()}  "
                          f"schema={tbl.schema}  key={tbl.search_key!r}")
        else:
            self._require_db(db_name)
            tables = self.databases[db_name]
            print(f"Database: {db_name}  ({len(tables)} table(s))")
            for tname, tbl in tables.items():
                print(f"  └─ {tname}  rows={tbl.count()}  "
                      f"schema={tbl.schema}  key={tbl.search_key!r}")

    def _require_db(self, db_name: str) -> None:
        if db_name not in self.databases:
            raise KeyError(f"Database '{db_name}' does not exist.")

    def _require_table(self, db_name: str, table_name: str) -> None:
        self._require_db(db_name)
        if table_name not in self.databases[db_name]:
            raise KeyError(
                f"Table '{table_name}' does not exist in database '{db_name}'."
            )

    def __repr__(self):
        db_list = self.list_databases()
        return f"DatabaseManager(databases={db_list})"
