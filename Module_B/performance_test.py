"""
Module B performance benchmark + EXPLAIN evidence generator.

This script creates reproducible before/after artifacts for:
1. key SELECT queries used by the current Flask app
2. index optimization impact
3. EXPLAIN FORMAT=JSON evidence
"""

from __future__ import annotations

import csv
import json
import os
import statistics
import time
from datetime import datetime, timezone

import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(BASE_DIR, "sql")
RESULTS_DIR = os.path.join(BASE_DIR, "performance", "results")

DROP_INDEXES_SQL = os.path.join(SQL_DIR, "drop_indexes.sql")
CREATE_INDEXES_SQL = os.path.join(SQL_DIR, "create_indexes.sql")


QUERY_CASES = [
    {
        "query_id": "LOGIN_QUERY",
        "description": "Auth lookup join by username",
        "query": """
            SELECT
                m.member_id,
                m.name,
                m.email,
                m.contact_number,
                m.address,
                c.username,
                c.password_hash,
                GROUP_CONCAT(DISTINCT r.role_code ORDER BY r.role_code) AS role_codes
            FROM Credentials c
            JOIN members m
              ON m.member_id = c.member_id
            LEFT JOIN member_roles mr
              ON mr.member_id = m.member_id
            LEFT JOIN roles r
              ON r.role_id = mr.role_id
            WHERE c.username = %s
            GROUP BY
                m.member_id,
                m.name,
                m.email,
                m.contact_number,
                m.address,
                c.username,
                c.password_hash
        """,
        "params": ("admin",),
        "iterations": 200,
    },
    {
        "query_id": "ADMIN_CHECK_QUERY",
        "description": "RBAC admin membership check",
        "query": """
            SELECT 1 AS is_admin
            FROM member_roles mr
            JOIN roles r
              ON r.role_id = mr.role_id
            WHERE mr.member_id = %s
              AND UPPER(r.role_code) = 'ADMIN'
            LIMIT 1
        """,
        "params": (28,),
        "iterations": 400,
    },
    {
        "query_id": "USER_TICKETS_QUERY",
        "description": "User ticket listing with filter + order",
        "query": """
            SELECT ticket_id, title, description, member_id, location_id, category_id,
                   priority, status_id, created_at, updated_at
            FROM tickets
            WHERE member_id = %s
            ORDER BY created_at DESC
        """,
        "params": (2,),
        "iterations": 300,
    },
    {
        "query_id": "ADMIN_TICKETS_QUERY",
        "description": "Admin ticket listing ordered by created_at",
        "query": """
            SELECT ticket_id, title, description, member_id, location_id, category_id,
                   priority, status_id, created_at, updated_at
            FROM tickets
            ORDER BY created_at DESC
        """,
        "params": (),
        "iterations": 150,
    },
]


def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def p95(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(0.95 * (len(ordered) - 1))
    return ordered[idx]


def ensure_dirs():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def execute_sql_file(connection, path):
    with open(path, "r", encoding="utf-8") as sql_file:
        sql = sql_file.read()

    statements = []
    current = []
    in_single = False
    in_double = False
    in_backtick = False
    escape_next = False

    for ch in sql:
        if escape_next:
            current.append(ch)
            escape_next = False
            continue

        if ch == "\\" and (in_single or in_double):
            current.append(ch)
            escape_next = True
            continue

        if ch == "'" and not in_double and not in_backtick:
            in_single = not in_single
            current.append(ch)
            continue

        if ch == '"' and not in_single and not in_backtick:
            in_double = not in_double
            current.append(ch)
            continue

        if ch == "`" and not in_single and not in_double:
            in_backtick = not in_backtick
            current.append(ch)
            continue

        if ch == ";" and not in_single and not in_double and not in_backtick:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            continue

        current.append(ch)

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)

    cursor = connection.cursor(buffered=True)
    try:
        for statement in statements:
            cursor.execute(statement)
            if cursor.with_rows:
                cursor.fetchall()
        connection.commit()
    finally:
        cursor.close()


def run_query_timing(connection, query, params, iterations):
    durations = []
    with connection.cursor() as cursor:
        for _ in range(iterations):
            start = time.perf_counter()
            cursor.execute(query, params)
            cursor.fetchall()
            end = time.perf_counter()
            durations.append((end - start) * 1000.0)
    return durations


def run_explain_json(connection, query, params):
    explain_sql = "EXPLAIN FORMAT=JSON " + query
    with connection.cursor() as cursor:
        cursor.execute(explain_sql, params)
        row = cursor.fetchone()
    plan_text = row[0] if row else "{}"
    try:
        return json.loads(plan_text)
    except json.JSONDecodeError:
        return {"raw_plan": plan_text}


def collect_phase(connection, phase_name):
    timing_rows = []
    explain_rows = []

    for case in QUERY_CASES:
        durations = run_query_timing(
            connection=connection,
            query=case["query"],
            params=case["params"],
            iterations=case["iterations"],
        )
        timing_rows.append(
            {
                "phase": phase_name,
                "query_id": case["query_id"],
                "description": case["description"],
                "iterations": case["iterations"],
                "avg_ms": round(statistics.mean(durations), 6),
                "min_ms": round(min(durations), 6),
                "max_ms": round(max(durations), 6),
                "p95_ms": round(p95(durations), 6),
                "captured_at_utc": utc_now_iso(),
            }
        )

        explain_rows.append(
            {
                "phase": phase_name,
                "query_id": case["query_id"],
                "description": case["description"],
                "query": " ".join(case["query"].split()),
                "params": list(case["params"]),
                "captured_at_utc": utc_now_iso(),
                "plan": run_explain_json(connection, case["query"], case["params"]),
            }
        )

    return timing_rows, explain_rows


def write_timing_csv(path, rows):
    headers = [
        "phase",
        "query_id",
        "description",
        "iterations",
        "avg_ms",
        "min_ms",
        "max_ms",
        "p95_ms",
        "captured_at_utc",
    ]
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2)


def write_summary(before_rows, after_rows, path):
    before_map = {row["query_id"]: row for row in before_rows}
    after_map = {row["query_id"]: row for row in after_rows}

    lines = [
        "# Module B Benchmark Summary",
        "",
        f"Generated at (UTC): {utc_now_iso()}",
        "",
        "| Query | Before Avg (ms) | After Avg (ms) | Improvement |",
        "|---|---:|---:|---:|",
    ]

    for query_id in before_map:
        before = before_map[query_id]["avg_ms"]
        after = after_map[query_id]["avg_ms"]
        improvement = ((before - after) / before * 100.0) if before else 0.0
        lines.append(f"| {query_id} | {before:.6f} | {after:.6f} | {improvement:.2f}% |")

    with open(path, "w", encoding="utf-8") as summary_file:
        summary_file.write("\n".join(lines) + "\n")


def main():
    ensure_dirs()

    connection = None
    try:
        connection = get_connection()

        print("Running baseline phase (drop indexes)...")
        execute_sql_file(connection, DROP_INDEXES_SQL)
        before_timing, before_explain = collect_phase(connection, "before")

        print("Running indexed phase (create indexes)...")
        execute_sql_file(connection, CREATE_INDEXES_SQL)
        after_timing, after_explain = collect_phase(connection, "after")

        write_timing_csv(os.path.join(RESULTS_DIR, "timings_before.csv"), before_timing)
        write_timing_csv(os.path.join(RESULTS_DIR, "timings_after.csv"), after_timing)
        write_json(os.path.join(RESULTS_DIR, "explain_before.json"), before_explain)
        write_json(os.path.join(RESULTS_DIR, "explain_after.json"), after_explain)
        write_summary(before_timing, after_timing, os.path.join(RESULTS_DIR, "summary.md"))

        print("Benchmark artifacts generated:")
        print(f"- {os.path.join(RESULTS_DIR, 'timings_before.csv')}")
        print(f"- {os.path.join(RESULTS_DIR, 'timings_after.csv')}")
        print(f"- {os.path.join(RESULTS_DIR, 'explain_before.json')}")
        print(f"- {os.path.join(RESULTS_DIR, 'explain_after.json')}")
        print(f"- {os.path.join(RESULTS_DIR, 'summary.md')}")

    except Error as exc:
        print(f"Database error: {exc}")
        raise
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
