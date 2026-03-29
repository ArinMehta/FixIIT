from __future__ import annotations

import csv
import os
import random
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from custom_engine.models import init_fixiit_db, storage_path_from_repo


def run_custom_engine_workload(total_requests: int = 200, workers: int = 16, fail_ratio: float = 0.1):
    db = init_fixiit_db(storage_path_from_repo())

    latencies = []
    commit_count = 0
    rollback_count = 0
    lock = threading.Lock()

    def one_request(i: int):
        nonlocal commit_count, rollback_count
        t0 = time.perf_counter()
        assignment_id = 100 + i

        try:
            # Replicate the ACID demo: assign random ticket to random technician
            tx = db.begin()
            
            # Safe IDs based on bootstrap data (members: 1,2,3,17,28; tickets: 1,2,3)
            ticket_id = (i % 3) + 1
            tech_id_options = [17]  # Electrician A
            admin_id = 28
            
            ticket = tx.get("tickets", ticket_id)
            tech = tx.get("members", tech_id_options[i % len(tech_id_options)])
            admin = tx.get("members", admin_id)
            
            if ticket is None or tech is None or admin is None:
                raise RuntimeError("Missing base data for assignment")

            # Update ticket status
            fail_injected = random.random() < fail_ratio
            fail_after_ops = 2 if fail_injected else None

            updated_ticket = dict(ticket)
            updated_ticket["status_id"] = 2
            tx.update("tickets", ticket_id, updated_ticket)
            
            tx.insert(
                "assignments",
                {
                    "assignment_id": assignment_id,
                    "ticket_id": ticket_id,
                    "technician_member_id": tech_id_options[i % len(tech_id_options)],
                    "assigned_by": admin_id,
                    "instructions": f"Assignment {i}",
                },
            )
            tx.commit(fail_after_ops=fail_after_ops)
            with lock:
                commit_count += 1
        except Exception:
            with lock:
                rollback_count += 1
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            with lock:
                latencies.append(elapsed_ms)

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(one_request, i) for i in range(total_requests)]
        for f in as_completed(futures):
            f.result()
    total_s = time.perf_counter() - start

    result = {
        "backend": "custom_bplustree",
        "requests": total_requests,
        "workers": workers,
        "commits": commit_count,
        "rollbacks": rollback_count,
        "total_time_s": round(total_s, 6),
        "throughput_rps": round(total_requests / total_s, 3) if total_s else 0.0,
        "avg_ms": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "p95_ms": round(percentile(latencies, 95), 3) if latencies else 0.0,
        "status": "ok",
    }
    return result


def percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    idx = min(len(values) - 1, int(round((p / 100.0) * (len(values) - 1))))
    return values[idx]


def run_sql_workload(total_requests: int = 200, workers: int = 16):
    module_b_path = Path(__file__).resolve().parents[1] / "Assignment_2" / "Module_B"
    if not module_b_path.exists():
        return {
            "backend": "mysql_sql",
            "requests": total_requests,
            "workers": workers,
            "status": "skipped",
            "reason": "Module_B not found",
        }

    try:
        import mysql.connector  # noqa: F401

        import sys

        if str(module_b_path) not in sys.path:
            sys.path.append(str(module_b_path))
        from config import DB_CONFIG  # type: ignore
    except Exception as exc:
        return {
            "backend": "mysql_sql",
            "requests": total_requests,
            "workers": workers,
            "status": "skipped",
            "reason": f"Missing SQL dependencies/config: {exc}",
        }

    latencies = []
    errors = 0
    first_error = None
    lock = threading.Lock()

    query = """
        SELECT ticket_id, member_id, status_id
        FROM tickets
        WHERE member_id = %s
        ORDER BY created_at DESC
        LIMIT 20
    """

    def one_request(_):
        nonlocal errors, first_error
        t0 = time.perf_counter()
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(query, (2,))
            cur.fetchall()
            cur.close()
            conn.close()
        except Exception as exc:
            with lock:
                errors += 1
                if first_error is None:
                    first_error = str(exc)
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            with lock:
                latencies.append(elapsed_ms)

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(one_request, i) for i in range(total_requests)]
        for f in as_completed(futures):
            f.result()
    total_s = time.perf_counter() - start

    payload = {
        "backend": "mysql_sql",
        "requests": total_requests,
        "workers": workers,
        "errors": errors,
        "total_time_s": round(total_s, 6),
        "throughput_rps": round(total_requests / total_s, 3) if total_s else 0.0,
        "avg_ms": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "p95_ms": round(percentile(latencies, 95), 3) if latencies else 0.0,
        "status": "ok" if errors < total_requests else "failed",
    }
    if first_error is not None:
        payload["reason"] = first_error
    return payload


def write_results(results, output_csv: Path):
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    headers = sorted({k for row in results for k in row.keys()})
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)


def main():
    random.seed(432)
    requests = int(os.getenv("A3_REQUESTS", "200"))
    workers = int(os.getenv("A3_WORKERS", "16"))

    custom = run_custom_engine_workload(total_requests=requests, workers=workers)
    sql = run_sql_workload(total_requests=requests, workers=workers)

    results = [custom, sql]
    out_csv = Path(__file__).resolve().parent / "results" / "backend_comparison.csv"
    write_results(results, out_csv)

    print("=== Assignment 3 Backend Comparison ===")
    for row in results:
        print(row)
    print(f"Saved: {out_csv}")


if __name__ == "__main__":
    main()
