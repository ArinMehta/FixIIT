# Module B Performance Artifacts

This folder stores reproducible benchmark and EXPLAIN artifacts.

## Run

From `Module_B`:

```bash
python performance_test.py
```

## Generated Files (`performance/results/`)

- `timings_before.csv` - query timings after dropping optimization indexes
- `timings_after.csv` - query timings after creating optimization indexes
- `explain_before.json` - EXPLAIN FORMAT=JSON output before indexes
- `explain_after.json` - EXPLAIN FORMAT=JSON output after indexes
- `summary.md` - before/after comparison table

## Notes

- The script uses real query shapes from current backend code:
  - login/auth lookup
  - admin role check
  - user tickets listing
  - admin tickets listing
- Index scripts used:
  - `sql/drop_indexes.sql`
  - `sql/create_indexes.sql`
