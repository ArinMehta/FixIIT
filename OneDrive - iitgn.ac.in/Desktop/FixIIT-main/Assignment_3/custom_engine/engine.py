from __future__ import annotations

import copy
import json
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_A_DB_PATH = REPO_ROOT / "Assignment_2" / "Module_A" / "db_management_system" / "database"
if str(MODULE_A_DB_PATH) not in sys.path:
    sys.path.append(str(MODULE_A_DB_PATH))

from table import Table  # type: ignore  # noqa: E402


ValidatorFn = Callable[[Dict[str, Dict[object, dict]]], None]


@dataclass
class Operation:
    op: str
    table: str
    key: object
    value: Optional[dict]


class TransactionContext:
    def __init__(self, db: "TransactionalBPlusDatabase", tx_id: str):
        self._db = db
        self.tx_id = tx_id
        self._closed = False

    def insert(self, table: str, record: dict) -> None:
        self._assert_open()
        self._db._stage_insert(self.tx_id, table, record)

    def update(self, table: str, key: object, record: dict) -> None:
        self._assert_open()
        self._db._stage_update(self.tx_id, table, key, record)

    def delete(self, table: str, key: object) -> None:
        self._assert_open()
        self._db._stage_delete(self.tx_id, table, key)

    def get(self, table: str, key: object) -> Optional[dict]:
        self._assert_open()
        return self._db._read_with_staged(self.tx_id, table, key)

    def commit(self, fail_after_ops: Optional[int] = None) -> None:
        self._assert_open()
        self._db.commit(self.tx_id, fail_after_ops=fail_after_ops)
        self._closed = True

    def rollback(self) -> None:
        if not self._closed:
            self._db.rollback(self.tx_id)
            self._closed = True

    def _assert_open(self) -> None:
        if self._closed:
            raise RuntimeError(f"Transaction {self.tx_id} is already closed")


class TransactionalBPlusDatabase:
    def __init__(self, storage_dir: str, order: int = 8):
        self.storage_dir = Path(storage_dir)
        self.tables_dir = self.storage_dir / "tables"
        self.wal_path = self.storage_dir / "wal.jsonl"
        self.meta_path = self.storage_dir / "metadata.json"

        self.order = order
        self.tables: Dict[str, Table] = {}
        self.validators: List[ValidatorFn] = []

        self._tx_state: Dict[str, List[Operation]] = {}
        self._lock = threading.RLock()

        self._ensure_storage()
        self._load_from_disk()
        self.recover()

    def _ensure_storage(self) -> None:
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        if not self.wal_path.exists():
            self.wal_path.write_text("", encoding="utf-8")
        if not self.meta_path.exists():
            self.meta_path.write_text(json.dumps({"tables": {}}, indent=2), encoding="utf-8")

    def create_table(self, table_name: str, schema: dict, search_key: str) -> None:
        if table_name in self.tables:
            raise ValueError(f"Table '{table_name}' already exists")

        table = Table(name=table_name, schema=dict(schema), order=self.order, search_key=search_key)
        self.tables[table_name] = table
        self._persist_metadata()
        self._persist_all_tables()

    def begin(self) -> TransactionContext:
        tx_id = f"tx-{uuid.uuid4().hex[:12]}"
        self._tx_state[tx_id] = []
        self._write_wal({"type": "BEGIN", "tx_id": tx_id, "ts": time.time()})
        return TransactionContext(self, tx_id)

    def rollback(self, tx_id: str) -> None:
        if tx_id not in self._tx_state:
            return
        self._tx_state.pop(tx_id, None)
        self._write_wal({"type": "ABORT", "tx_id": tx_id, "ts": time.time(), "reason": "manual_rollback"})

    def commit(self, tx_id: str, fail_after_ops: Optional[int] = None) -> None:
        if tx_id not in self._tx_state:
            raise KeyError(f"Unknown transaction '{tx_id}'")

        staged_ops = self._tx_state[tx_id]
        if not staged_ops:
            self._write_wal({"type": "COMMIT", "tx_id": tx_id, "ts": time.time(), "op_count": 0})
            self._tx_state.pop(tx_id, None)
            return

        with self._lock:
            snapshot_before = self._snapshot_state()
            simulated_state = copy.deepcopy(snapshot_before)
            self._apply_ops_to_state(simulated_state, staged_ops)
            self._run_validators(simulated_state)

            applied_count = 0
            try:
                for op in staged_ops:
                    before = self._get_state_record(snapshot_before, op.table, op.key)
                    after = self._get_state_record(simulated_state, op.table, op.key)

                    self._write_wal(
                        {
                            "type": "APPLY",
                            "tx_id": tx_id,
                            "ts": time.time(),
                            "table": op.table,
                            "key": op.key,
                            "before": before,
                            "after": after,
                        }
                    )
                    self._apply_operation_to_table(op)
                    applied_count += 1

                    if fail_after_ops is not None and applied_count >= fail_after_ops:
                        raise RuntimeError(f"Injected failure after {applied_count} operation(s)")

                self._write_wal({"type": "COMMIT", "tx_id": tx_id, "ts": time.time(), "op_count": len(staged_ops)})
                self._persist_all_tables()
                self._tx_state.pop(tx_id, None)
            except Exception as exc:
                self._restore_snapshot(snapshot_before)
                self._persist_all_tables()
                self._write_wal(
                    {
                        "type": "ABORT",
                        "tx_id": tx_id,
                        "ts": time.time(),
                        "reason": str(exc),
                        "applied_count": applied_count,
                    }
                )
                self._tx_state.pop(tx_id, None)
                raise

    def get(self, table_name: str, key: object) -> Optional[dict]:
        self._require_table(table_name)
        result = self.tables[table_name].get(key)
        return dict(result) if result is not None else None

    def get_all(self, table_name: str) -> List[dict]:
        self._require_table(table_name)
        return [dict(r) for r in self.tables[table_name].get_all()]

    def register_validator(self, validator: ValidatorFn) -> None:
        self.validators.append(validator)

    def recover(self) -> None:
        logs = self._read_wal()
        if not logs:
            return

        by_tx: Dict[str, Dict[str, object]] = {}
        for rec in logs:
            tx_id = rec.get("tx_id")
            if not tx_id:
                continue
            if tx_id not in by_tx:
                by_tx[tx_id] = {"status": "OPEN", "applies": []}
            if rec.get("type") == "APPLY":
                by_tx[tx_id]["applies"].append(rec)
            elif rec.get("type") == "COMMIT":
                by_tx[tx_id]["status"] = "COMMITTED"
            elif rec.get("type") == "ABORT":
                by_tx[tx_id]["status"] = "ABORTED"

        changed = False
        for tx_id, tx_data in by_tx.items():
            status = tx_data["status"]
            applies = tx_data["applies"]
            if status == "COMMITTED":
                for rec in applies:
                    self._apply_after_image(rec)
                    changed = True
            else:
                for rec in reversed(applies):
                    self._apply_before_image(rec)
                    changed = True

        if changed:
            self._persist_all_tables()

    def _stage_insert(self, tx_id: str, table_name: str, record: dict) -> None:
        self._require_tx(tx_id)
        self._require_table(table_name)

        table = self.tables[table_name]
        candidate = dict(record)
        table.validate_record(candidate)
        key = candidate[table.search_key]

        current = self._read_with_staged(tx_id, table_name, key)
        if current is not None:
            raise ValueError(f"Duplicate key '{key}' in table '{table_name}'")

        self._tx_state[tx_id].append(Operation(op="upsert", table=table_name, key=key, value=candidate))

    def _stage_update(self, tx_id: str, table_name: str, key: object, record: dict) -> None:
        self._require_tx(tx_id)
        self._require_table(table_name)

        table = self.tables[table_name]
        candidate = dict(record)
        table.validate_record(candidate)
        if candidate.get(table.search_key) != key:
            raise ValueError("Primary key in update record must match provided key")

        current = self._read_with_staged(tx_id, table_name, key)
        if current is None:
            raise KeyError(f"Record '{key}' not found in '{table_name}'")

        self._tx_state[tx_id].append(Operation(op="upsert", table=table_name, key=key, value=candidate))

    def _stage_delete(self, tx_id: str, table_name: str, key: object) -> None:
        self._require_tx(tx_id)
        self._require_table(table_name)

        current = self._read_with_staged(tx_id, table_name, key)
        if current is None:
            raise KeyError(f"Record '{key}' not found in '{table_name}'")

        self._tx_state[tx_id].append(Operation(op="delete", table=table_name, key=key, value=None))

    def _read_with_staged(self, tx_id: str, table_name: str, key: object) -> Optional[dict]:
        self._require_tx(tx_id)
        self._require_table(table_name)

        value = self.tables[table_name].get(key)
        local = dict(value) if value is not None else None

        for op in self._tx_state[tx_id]:
            if op.table == table_name and op.key == key:
                if op.op == "delete":
                    local = None
                else:
                    local = dict(op.value)
        return local

    def _apply_operation_to_table(self, op: Operation) -> None:
        table = self.tables[op.table]
        if op.op == "delete":
            table.delete(op.key)
        else:
            existing = table.get(op.key)
            if existing is None:
                table.insert(dict(op.value))
            else:
                table.update(op.key, dict(op.value))

    def _snapshot_state(self) -> Dict[str, Dict[object, dict]]:
        state: Dict[str, Dict[object, dict]] = {}
        for table_name, table in self.tables.items():
            key_name = table.search_key
            state[table_name] = {}
            for rec in table.get_all():
                state[table_name][rec[key_name]] = dict(rec)
        return state

    def _restore_snapshot(self, state: Dict[str, Dict[object, dict]]) -> None:
        for table_name, table_state in state.items():
            meta = self._table_meta()[table_name]
            rebuilt = Table(
                name=table_name,
                schema=dict(meta["schema"]),
                order=int(meta["order"]),
                search_key=meta["search_key"],
            )
            for rec in table_state.values():
                rebuilt.insert(dict(rec))
            self.tables[table_name] = rebuilt

    def _apply_ops_to_state(self, state: Dict[str, Dict[object, dict]], ops: List[Operation]) -> None:
        for op in ops:
            table_map = state[op.table]
            if op.op == "delete":
                table_map.pop(op.key, None)
            else:
                table_map[op.key] = dict(op.value)

    def _run_validators(self, state: Dict[str, Dict[object, dict]]) -> None:
        for validator in self.validators:
            validator(state)

    def _get_state_record(self, state: Dict[str, Dict[object, dict]], table: str, key: object) -> Optional[dict]:
        value = state[table].get(key)
        return dict(value) if value is not None else None

    def _persist_metadata(self) -> None:
        payload = {"tables": self._table_meta()}
        self.meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._fsync_path(self.meta_path)

    def _table_meta(self) -> Dict[str, dict]:
        return {
            name: {
                "schema": table.schema,
                "search_key": table.search_key,
                "order": table.order,
            }
            for name, table in self.tables.items()
        }

    def _persist_all_tables(self) -> None:
        self._persist_metadata()
        for table_name, table in self.tables.items():
            payload = {
                "schema": table.schema,
                "search_key": table.search_key,
                "order": table.order,
                "records": table.get_all(),
            }
            path = self.tables_dir / f"{table_name}.json"
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            self._fsync_path(path)

    def _load_from_disk(self) -> None:
        if not self.meta_path.exists():
            return

        try:
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {"tables": {}}

        table_meta = meta.get("tables", {})
        for table_name, entry in table_meta.items():
            table = Table(
                name=table_name,
                schema=dict(entry["schema"]),
                order=int(entry["order"]),
                search_key=entry["search_key"],
            )

            table_file = self.tables_dir / f"{table_name}.json"
            if table_file.exists():
                data = json.loads(table_file.read_text(encoding="utf-8"))
                for rec in data.get("records", []):
                    table.insert(dict(rec))
            self.tables[table_name] = table

    def _read_wal(self) -> List[dict]:
        entries = []
        for line in self.wal_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def _write_wal(self, record: dict) -> None:
        with self.wal_path.open("a", encoding="utf-8") as wal_file:
            wal_file.write(json.dumps(record, separators=(",", ":")) + "\n")
            wal_file.flush()
            os.fsync(wal_file.fileno())

    def _apply_after_image(self, rec: dict) -> None:
        table_name = rec["table"]
        key = rec["key"]
        after = rec.get("after")
        table = self.tables[table_name]

        if after is None:
            table.delete(key)
            return

        existing = table.get(key)
        if existing is None:
            table.insert(dict(after))
        else:
            table.update(key, dict(after))

    def _apply_before_image(self, rec: dict) -> None:
        table_name = rec["table"]
        key = rec["key"]
        before = rec.get("before")
        table = self.tables[table_name]

        if before is None:
            table.delete(key)
            return

        existing = table.get(key)
        if existing is None:
            table.insert(dict(before))
        else:
            table.update(key, dict(before))

    def _require_table(self, table_name: str) -> None:
        if table_name not in self.tables:
            raise KeyError(f"Table '{table_name}' does not exist")

    def _require_tx(self, tx_id: str) -> None:
        if tx_id not in self._tx_state:
            raise KeyError(f"Transaction '{tx_id}' does not exist")

    @staticmethod
    def _fsync_path(path: Path) -> None:
        with path.open("r+b") as handle:
            handle.flush()
            os.fsync(handle.fileno())
