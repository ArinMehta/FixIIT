"""
db_manager.py
-------------
DatabaseManager that manages multiple databases and their tables.
PerformanceAnalyzer compares B+ Tree vs BruteForceDB across all operations.
"""

from __future__ import annotations
import time
import tracemalloc
import random
from typing import Any, Dict, List, Optional, Tuple

from .table import Table
from .bruteforce import BruteForceDB


# ---------------------------------------------------------------------------
# Performance Analyser
# ---------------------------------------------------------------------------

class PerformanceAnalyzer:
    """
    Compares B+ Tree (via DatabaseManager) against BruteForceDB across
    insert, search, delete, range-query, and random-mixed workloads.
    Also measures peak memory usage.
    """

    def __init__(self, db_manager: "DatabaseManager") -> None:
        self.db = db_manager
        # Internal benchmark database — created once, reused across benchmarks
        if "_bench_db" not in self.db.databases:
            self.db.create_database("_bench_db")

    # ------------------------------------------------------------------
    # Timing / memory helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _time_it(fn) -> Tuple[Any, float]:
        """Return (result, elapsed_seconds)."""
        start = time.perf_counter()
        result = fn()
        return result, time.perf_counter() - start

    @staticmethod
    def _memory_it(fn) -> Tuple[Any, int]:
        """Return (result, peak_memory_bytes)."""
        tracemalloc.start()
        result = fn()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return result, peak

    # ------------------------------------------------------------------
    # Benchmark helpers
    # ------------------------------------------------------------------

    def _make_bench_table(self, table_name: str, pk: str) -> Table:
        """Drop-and-recreate a benchmark table in the internal bench db."""
        db_name = "_bench_db"
        try:
            self.db.delete_table(db_name, table_name)
        except KeyError:
            pass
        schema = {pk: int, "value": int}
        table, _ = self.db.create_table(db_name, table_name, schema,
                                         order=8, search_key=pk)
        return table

    # ------------------------------------------------------------------
    # Single-operation benchmarks
    # ------------------------------------------------------------------

    def benchmark_insert(
        self,
        keys: List[Any],
        table_name: str = "_bench_insert",
    ) -> Dict[str, float]:
        pk = "id"
        table = self._make_bench_table(table_name, pk)

        _, bpt_time = self._time_it(
            lambda: [table.insert({pk: k, "value": k * 2}) for k in keys]
        )

        bf = BruteForceDB()
        _, bf_time = self._time_it(
            lambda: [bf.insert(k, {pk: k, "value": k * 2}) for k in keys]
        )

        return {"bptree_insert_time": bpt_time, "bruteforce_insert_time": bf_time}

    def benchmark_search(
        self,
        keys: List[Any],
        search_keys: List[Any],
        table_name: str = "_bench_search",
    ) -> Dict[str, float]:
        pk = "id"
        table = self._make_bench_table(table_name, pk)
        for k in keys:
            table.insert({pk: k, "value": k * 2})

        bf = BruteForceDB()
        for k in keys:
            bf.insert(k, {pk: k, "value": k * 2})

        _, bpt_time = self._time_it(
            lambda: [table.get(k) for k in search_keys]
        )
        _, bf_time = self._time_it(
            lambda: [bf.search(k) for k in search_keys]
        )

        return {"bptree_search_time": bpt_time, "bruteforce_search_time": bf_time}

    def benchmark_delete(
        self,
        keys: List[Any],
        delete_keys: List[Any],
        table_name: str = "_bench_delete",
    ) -> Dict[str, float]:
        pk = "id"
        table = self._make_bench_table(table_name, pk)
        for k in keys:
            table.insert({pk: k, "value": k * 2})

        bf = BruteForceDB()
        for k in keys:
            bf.insert(k, {pk: k, "value": k * 2})

        _, bpt_time = self._time_it(
            lambda: [table.delete(k) for k in delete_keys]
        )
        _, bf_time = self._time_it(
            lambda: [bf.delete(k) for k in delete_keys]
        )

        return {"bptree_delete_time": bpt_time, "bruteforce_delete_time": bf_time}

    def benchmark_range_query(
        self,
        keys: List[Any],
        low: Any,
        high: Any,
        table_name: str = "_bench_range",
    ) -> Dict[str, float]:
        pk = "id"
        table = self._make_bench_table(table_name, pk)
        for k in keys:
            table.insert({pk: k, "value": k * 2})

        bf = BruteForceDB()
        for k in keys:
            bf.insert(k, {pk: k, "value": k * 2})

        _, bpt_time = self._time_it(
            lambda: table.range_query(low, high)
        )
        _, bf_time = self._time_it(
            lambda: bf.range_query(low, high)
        )

        return {"bptree_range_time": bpt_time, "bruteforce_range_time": bf_time}

    def benchmark_memory(
        self,
        keys: List[Any],
        table_name: str = "_bench_mem",
    ) -> Dict[str, int]:
        pk = "id"

        def build_bptree():
            table = self._make_bench_table(table_name, pk)
            for k in keys:
                table.insert({pk: k, "value": k * 2})

        def build_bf():
            bf = BruteForceDB()
            for k in keys:
                bf.insert(k, {pk: k, "value": k * 2})

        _, bpt_mem = self._memory_it(build_bptree)
        _, bf_mem  = self._memory_it(build_bf)

        return {"bptree_peak_memory_bytes": bpt_mem,
                "bruteforce_peak_memory_bytes": bf_mem}

    def benchmark_random(
        self,
        n_ops: int = 500,
        key_range: int = 10000,
        table_name: str = "_bench_random",
    ) -> Dict[str, float]:
        """Mixed workload: insert, search, delete in random order."""
        pk = "id"
        table = self._make_bench_table(table_name, pk)
        bf = BruteForceDB()
        ops = ["insert", "search", "delete"]

        def run_bptree():
            for _ in range(n_ops):
                op  = random.choice(ops)
                key = random.randint(1, key_range)
                if op == "insert":
                    try:
                        table.insert({pk: key, "value": key})
                    except Exception:
                        pass
                elif op == "search":
                    table.get(key)
                else:
                    table.delete(key)

        def run_bf():
            for _ in range(n_ops):
                op  = random.choice(ops)
                key = random.randint(1, key_range)
                if op == "insert":
                    bf.insert(key, {pk: key, "value": key})
                elif op == "search":
                    bf.search(key)
                else:
                    bf.delete(key)

        _, bpt_time = self._time_it(run_bptree)
        _, bf_time  = self._time_it(run_bf)

        return {"bptree_random_time": bpt_time, "bruteforce_random_time": bf_time}

    # ------------------------------------------------------------------
    # Full automated benchmark suite
    # ------------------------------------------------------------------

    def run_full_benchmark(
        self,
        sizes: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Run all benchmarks across multiple dataset sizes."""
        sizes = sizes or [100, 500, 1_000, 5_000, 10_000]
        results = []
        for n in sizes:
            keys        = random.sample(range(1, n * 10), n)
            search_keys = random.sample(keys, min(100, n))
            delete_keys = random.sample(keys, min(50, n))
            lo = min(keys)
            hi = lo + (max(keys) - lo) // 2

            row: Dict[str, Any] = {"n": n}
            row.update(self.benchmark_insert(list(keys)))
            row.update(self.benchmark_search(list(keys), search_keys))
            row.update(self.benchmark_delete(list(keys), delete_keys))
            row.update(self.benchmark_range_query(list(keys), lo, hi))
            row.update(self.benchmark_memory(list(keys)))
            row.update(self.benchmark_random(n_ops=min(n, 500)))
            results.append(row)
        return results

    # ------------------------------------------------------------------
    # Plot all benchmarks
    # ------------------------------------------------------------------

    def plot_all(self, sizes=None):
        import matplotlib.pyplot as plt

        sizes = sizes or [100, 500, 1000, 2000, 5000]

        bpt_ins, bf_ins   = [], []
        bpt_srch, bf_srch = [], []
        bpt_del, bf_del   = [], []
        bpt_rng, bf_rng   = [], []
        bpt_mem, bf_mem   = [], []

        for n in sizes:
            keys        = random.sample(range(1, n * 10), n)
            search_keys = random.sample(keys, min(100, n))
            delete_keys = random.sample(keys, min(50, n))
            lo = min(keys)
            hi = lo + (max(keys) - lo) // 2

            r = self.benchmark_insert(list(keys))
            bpt_ins.append(r["bptree_insert_time"])
            bf_ins.append(r["bruteforce_insert_time"])

            r = self.benchmark_search(list(keys), search_keys)
            bpt_srch.append(r["bptree_search_time"])
            bf_srch.append(r["bruteforce_search_time"])

            r = self.benchmark_delete(list(keys), delete_keys)
            bpt_del.append(r["bptree_delete_time"])
            bf_del.append(r["bruteforce_delete_time"])

            r = self.benchmark_range_query(list(keys), lo, hi)
            bpt_rng.append(r["bptree_range_time"])
            bf_rng.append(r["bruteforce_range_time"])

            r = self.benchmark_memory(list(keys))
            bpt_mem.append(r["bptree_peak_memory_bytes"] / 1024)
            bf_mem.append(r["bruteforce_peak_memory_bytes"] / 1024)

        fig, axes = plt.subplots(3, 2, figsize=(14, 15))
        fig.suptitle("B+ Tree vs BruteForceDB — Performance Analysis", fontsize=14)

        time_datasets = [
            (axes[0, 0], bpt_ins,  bf_ins,  "Insertion Time"),
            (axes[0, 1], bpt_srch, bf_srch, "Search Time"),
            (axes[1, 0], bpt_rng,  bf_rng,  "Range Query Time"),
            (axes[1, 1], bpt_del,  bf_del,  "Deletion Time"),
        ]
        for ax, bpt, bf, title in time_datasets:
            ax.plot(sizes, bpt, label="B+ Tree",    marker='o', markersize=3)
            ax.plot(sizes, bf,  label="BruteForce", marker='s', markersize=3)
            ax.set_title(title)
            ax.set_xlabel("Number of Keys")
            ax.set_ylabel("Time (seconds)")
            ax.legend()
            ax.grid(True, alpha=0.3)

        axes[2, 0].plot(sizes, bpt_mem, label="B+ Tree",    marker='o', markersize=3)
        axes[2, 0].plot(sizes, bf_mem,  label="BruteForce", marker='s', markersize=3)
        axes[2, 0].set_title("Memory Usage — Insertion (KB)")
        axes[2, 0].set_xlabel("Number of Keys")
        axes[2, 0].set_ylabel("Peak Memory (KB)")
        axes[2, 0].legend()
        axes[2, 0].grid(True, alpha=0.3)

        axes[2, 1].axis('off')

        plt.tight_layout()
        plt.savefig("performance_analysis.png", dpi=150, bbox_inches='tight')
        try:
            from IPython import get_ipython  # type: ignore
            if get_ipython() is not None:
                plt.show()
            else:
                plt.close()
        except Exception:
            plt.close()
        print("Saved → performance_analysis.png")


# ---------------------------------------------------------------------------
# Database Manager
# ---------------------------------------------------------------------------

class DatabaseManager:
    """
    Top-level API managing multiple databases, each containing named tables.
    Follows the TA template: two-level hierarchy {db_name: {table_name: Table}}.
    Methods return (result, message) tuples to match template notebook usage.
    """

    def __init__(self) -> None:
        self.databases: Dict[str, Dict[str, Table]] = {}

    # ------------------------------------------------------------------
    # Database-level DDL
    # ------------------------------------------------------------------

    def create_database(self, db_name: str) -> Tuple[bool, str]:
        if db_name in self.databases:
            raise ValueError(f"Database '{db_name}' already exists.")
        self.databases[db_name] = {}
        return True, f"Database '{db_name}' created."

    def delete_database(self, db_name: str) -> Tuple[bool, str]:
        if db_name not in self.databases:
            raise KeyError(f"Database '{db_name}' not found.")
        del self.databases[db_name]
        return True, f"Database '{db_name}' deleted."

    def list_databases(self) -> Tuple[List[str], str]:
        return list(self.databases.keys()), "OK"

    # ------------------------------------------------------------------
    # Table-level DDL
    # ------------------------------------------------------------------

    def create_table(
        self,
        db_name: str,
        table_name: str,
        schema: Dict[str, type],
        order: int = 8,
        search_key: str = None,
    ) -> Tuple[Table, str]:
        db = self._get_db(db_name)
        if table_name in db:
            raise ValueError(f"Table '{table_name}' already exists in '{db_name}'.")
        table = Table(table_name, schema, order=order, search_key=search_key)
        db[table_name] = table
        return table, f"Table '{table_name}' created."

    def delete_table(self, db_name: str, table_name: str) -> Tuple[bool, str]:
        db = self._get_db(db_name)
        if table_name not in db:
            raise KeyError(f"Table '{table_name}' not found in '{db_name}'.")
        del db[table_name]
        return True, f"Table '{table_name}' deleted."

    def list_tables(self, db_name: str) -> Tuple[List[str], str]:
        db = self._get_db(db_name)
        return list(db.keys()), "OK"

    def get_table(self, db_name: str, table_name: str) -> Tuple[Table, str]:
        db = self._get_db(db_name)
        if table_name not in db:
            raise KeyError(f"Table '{table_name}' not found in '{db_name}'.")
        return db[table_name], "OK"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_db(self, db_name: str) -> Dict[str, Table]:
        if db_name not in self.databases:
            raise KeyError(f"Database '{db_name}' not found.")
        return self.databases[db_name]

    def __repr__(self) -> str:
        dbs = {k: list(v.keys()) for k, v in self.databases.items()}
        return f"DatabaseManager(databases={dbs})"