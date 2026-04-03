import time
import random
import tracemalloc
import statistics
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from bplustree  import BPlusTree
from bruteforce import BruteForceDB




def _time_it(fn: Callable, *args, repeats: int = 1) -> float:
   
    elapsed = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(*args)
        elapsed.append(time.perf_counter() - t0)
    return statistics.mean(elapsed)


def _measure_memory(fn: Callable, *args) -> float:
    tracemalloc.start()
    fn(*args)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024          # convert bytes → KiB


#  PerformanceAnalyzer


class PerformanceAnalyzer:

    def __init__(
        self,
        sizes: list = None,
        seed: int = 42,
        bpt_order: int = 8,
    ):
        self.sizes     = sizes or [100, 500, 1000, 3000, 5000, 10000]
        self.seed      = seed
        self.bpt_order = bpt_order
        self.results   = {}         # {metric: {label: [values per size]}}

    #  Run all benchmarks 

    def run_all(self, verbose: bool = True) -> dict:

        if verbose:
            print("=" * 60)
            print(f"  Performance Analysis  (B+ Tree order={self.bpt_order})")
            print("=" * 60)

        self.results["insertion"]    = self.benchmark_insertion(verbose=verbose)
        self.results["search"]       = self.benchmark_search(verbose=verbose)
        self.results["deletion"]     = self.benchmark_deletion(verbose=verbose)
        self.results["range_query"]  = self.benchmark_range_query(verbose=verbose)
        self.results["memory"]       = self.benchmark_memory(verbose=verbose)
        self.results["random_ops"]   = self.benchmark_random_ops(verbose=verbose)

        if verbose:
            print("\nAll benchmarks complete.")
        return self.results

    #  Individual benchmarks

    def benchmark_insertion(self, verbose: bool = True) -> dict:
        """Measure total insertion time for each dataset size."""
        bpt_times, bf_times = [], []
        if verbose:
            print("\n[1/6] Insertion benchmark …")

        for n in self.sizes:
            keys = self._random_keys(n)
            values = list(range(n))

            # B+ Tree
            def do_bpt():
                t = BPlusTree(order=self.bpt_order)
                for k, v in zip(keys, values):
                    t.insert(k, v)

            # BruteForce
            def do_bf():
                db = BruteForceDB()
                for k, v in zip(keys, values):
                    db.insert(k, v)

            bpt_times.append(_time_it(do_bpt))
            bf_times.append(_time_it(do_bf))

            if verbose:
                print(f"  n={n:>6}: BPT={bpt_times[-1]*1000:7.2f} ms  "
                      f"BF={bf_times[-1]*1000:7.2f} ms")

        return {"B+ Tree": bpt_times, "BruteForce": bf_times}

    def benchmark_search(self, verbose: bool = True) -> dict:
        """Measure average per-query search time (100 random searches)."""
        bpt_times, bf_times = [], []
        if verbose:
            print("\n[2/6] Search benchmark …")

        for n in self.sizes:
            keys   = self._random_keys(n)
            queries = random.sample(keys, min(100, n))

            bpt = BPlusTree(order=self.bpt_order)
            bf  = BruteForceDB()
            for k in keys:
                bpt.insert(k, k)
                bf.insert(k, k)

            bpt_t = _time_it(lambda: [bpt.search(q) for q in queries])
            bf_t  = _time_it(lambda: [bf.search(q) for q in queries])

            bpt_times.append(bpt_t)
            bf_times.append(bf_t)

            if verbose:
                print(f"  n={n:>6}: BPT={bpt_times[-1]*1000:7.3f} ms  "
                      f"BF={bf_times[-1]*1000:7.3f} ms")

        return {"B+ Tree": bpt_times, "BruteForce": bf_times}

    def benchmark_deletion(self, verbose: bool = True) -> dict:
        """Measure total deletion time for 20% of records."""
        bpt_times, bf_times = [], []
        if verbose:
            print("\n[3/6] Deletion benchmark …")

        for n in self.sizes:
            keys        = self._random_keys(n)
            del_keys    = random.sample(keys, max(1, n // 5))

            bpt = BPlusTree(order=self.bpt_order)
            bf  = BruteForceDB()
            for k in keys:
                bpt.insert(k, k)
                bf.insert(k, k)

            bpt_t = _time_it(lambda: [bpt.delete(k) for k in del_keys])
            bf_t  = _time_it(lambda: [bf.delete(k) for k in del_keys])

            bpt_times.append(bpt_t)
            bf_times.append(bf_t)

            if verbose:
                print(f"  n={n:>6}: BPT={bpt_times[-1]*1000:7.2f} ms  "
                      f"BF={bf_times[-1]*1000:7.2f} ms")

        return {"B+ Tree": bpt_times, "BruteForce": bf_times}

    def benchmark_range_query(self, verbose: bool = True) -> dict:
        """Measure 20 range queries spanning ~10% of key space each."""
        bpt_times, bf_times = [], []
        if verbose:
            print("\n[4/6] Range query benchmark …")

        for n in self.sizes:
            keys     = self._random_keys(n)
            min_k, max_k = min(keys), max(keys)
            span     = (max_k - min_k) // 10 or 1
            ranges   = [(random.randint(min_k, max_k - span),) for _ in range(20)]
            ranges   = [(lo, lo + span) for (lo,) in ranges]

            bpt = BPlusTree(order=self.bpt_order)
            bf  = BruteForceDB()
            for k in keys:
                bpt.insert(k, k)
                bf.insert(k, k)

            bpt_t = _time_it(lambda: [bpt.range_query(lo, hi) for lo, hi in ranges])
            bf_t  = _time_it(lambda: [bf.range_query(lo, hi) for lo, hi in ranges])

            bpt_times.append(bpt_t)
            bf_times.append(bf_t)

            if verbose:
                print(f"  n={n:>6}: BPT={bpt_times[-1]*1000:7.2f} ms  "
                      f"BF={bf_times[-1]*1000:7.2f} ms")

        return {"B+ Tree": bpt_times, "BruteForce": bf_times}

    def benchmark_memory(self, verbose: bool = True) -> dict:
        """Measure peak memory (KiB) used during bulk insertion."""
        bpt_mem, bf_mem = [], []
        if verbose:
            print("\n[5/6] Memory benchmark …")

        for n in self.sizes:
            keys = self._random_keys(n)

            def build_bpt():
                t = BPlusTree(order=self.bpt_order)
                for k in keys:
                    t.insert(k, k)

            def build_bf():
                db = BruteForceDB()
                for k in keys:
                    db.insert(k, k)

            bpt_mem.append(_measure_memory(build_bpt))
            bf_mem.append(_measure_memory(build_bf))

            if verbose:
                print(f"  n={n:>6}: BPT={bpt_mem[-1]:7.1f} KiB  "
                      f"BF={bf_mem[-1]:7.1f} KiB")

        return {"B+ Tree": bpt_mem, "BruteForce": bf_mem}

    def benchmark_random_ops(self, verbose: bool = True, ops_per_size: int = 200) -> dict:
        
        bpt_times, bf_times = [], []
        if verbose:
            print("\n[6/6] Random operations benchmark …")

        random.seed(self.seed + 99)

        for n in self.sizes:
            keys = self._random_keys(n)
            bpt  = BPlusTree(order=self.bpt_order)
            bf   = BruteForceDB()
            for k in keys:
                bpt.insert(k, k)
                bf.insert(k, k)

            ops = []
            for _ in range(ops_per_size):
                op  = random.choice(["insert", "search", "delete"])
                key = random.randint(1, n * 2)
                ops.append((op, key))

            def run_bpt():
                for op, key in ops:
                    if op == "insert":
                        bpt.insert(key, key)
                    elif op == "search":
                        bpt.search(key)
                    else:
                        bpt.delete(key)

            def run_bf():
                for op, key in ops:
                    if op == "insert":
                        bf.insert(key, key)
                    elif op == "search":
                        bf.search(key)
                    else:
                        bf.delete(key)

            bpt_times.append(_time_it(run_bpt))
            bf_times.append(_time_it(run_bf))

            if verbose:
                print(f"  n={n:>6}: BPT={bpt_times[-1]*1000:7.2f} ms  "
                      f"BF={bf_times[-1]*1000:7.2f} ms")

        return {"B+ Tree": bpt_times, "BruteForce": bf_times}

    #  Plotting


    def plot_all(self, figsize=(18, 12), save_path: str = None):
   
        metrics = [
            ("insertion",   "Insertion Time (ms)",      "Total time to insert n keys"),
            ("search",      "Search Time (ms)",         "100 random lookups (search)"),
            ("deletion",    "Deletion Time (ms)",       "Deleting 20 % of keys"),
            ("range_query", "Range Query Time (ms)",    "20 range queries (10 % span)"),
            ("memory",      "Peak Memory (KiB)",        "Memory during bulk insert"),
            ("random_ops",  "Random Ops Time (ms)",     "200 mixed insert/search/delete"),
        ]

        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle(
            f"B+ Tree (order={self.bpt_order}) vs BruteForceDB — Performance Analysis",
            fontsize=15, fontweight="bold", y=1.01,
        )

        colors = {"B+ Tree": "#1f77b4", "BruteForce": "#d62728"}
        markers = {"B+ Tree": "o", "BruteForce": "s"}

        for ax, (metric, ylabel, subtitle) in zip(axes.flat, metrics):
            data = self.results.get(metric, {})
            for label, values in data.items():
                y = [v * 1000 if "Time" in ylabel else v for v in values]
                ax.plot(
                    self.sizes, y,
                    label=label,
                    color=colors.get(label, "gray"),
                    marker=markers.get(label, "^"),
                    linewidth=2, markersize=6,
                )
            ax.set_title(subtitle, fontsize=11)
            ax.set_xlabel("Dataset size (n)", fontsize=9)
            ax.set_ylabel(ylabel, fontsize=9)
            ax.legend(fontsize=8)
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.set_xticks(self.sizes)
            ax.tick_params(axis="x", rotation=30, labelsize=7)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"[OK] Performance plot saved to {save_path}")

        return fig

    def summary_table(self) -> None:
        """Print a formatted summary table of all results."""
        print("\n" + "=" * 72)
        print(f"{'Benchmark':<16}", end="")
        for n in self.sizes:
            print(f"{'n='+str(n):>10}", end="")
        print()

        for metric, data in self.results.items():
            for label, values in data.items():
                row_label = f"{metric}/{label}"[:30]
                scale = 1000 if metric != "memory" else 1
                unit  = "ms" if metric != "memory" else "KiB"
                print(f"{row_label:<32}", end="")
                for v in values:
                    print(f"{v*scale:>9.2f}{unit[:1]}", end="")
                print()
        print("=" * 72)



    def _random_keys(self, n: int) -> list:
        random.seed(self.seed)
        return random.sample(range(1, n * 10 + 1), n)
