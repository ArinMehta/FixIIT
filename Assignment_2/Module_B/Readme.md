# FixIIT Module B - Assignment 4 Sharding

This Module B backend now implements Assignment 4 sharding with a minimal-risk design that keeps the existing Flask + `mysql-connector` structure intact.

## Sharding Design

- Only the `tickets` table is sharded.
- All other tables remain unsharded in one coordinator database.
- The shard key is `member_id`.
- Partitioning strategy is hash-based sharding across 3 shards.
- Canonical routing formula:

```text
shard_idx = (member_id - 1) % 3
```

- Canonical shard mapping:

```text
shard_0 -> port 3307
shard_1 -> port 3308
shard_2 -> port 3309
```

- The coordinator database stores:
  - `members`
  - `roles`
  - `member_roles`
  - `categories`
  - `locations`
  - `statuses`
  - `Credentials`
  - `member_portfolio`
  - `ticket_locator`
  - coordinator `db_change_audit`
- Each ticket shard stores:
  - shard-local `tickets`
  - shard-local `db_change_audit`

## Why `member_id` Was Chosen

- `GET /tickets` is member-scoped, so routing by `member_id` guarantees one-shard reads.
- All tickets for one member stay on one shard.
- The routing function is deterministic and simple to demonstrate in coursework.
- `ticket_id` is not used as the shard key because admin update/delete resolve through `ticket_locator`, which remains correct after migration and for preserved legacy IDs.

## Coordinator Role

- The coordinator database is the authority for all unsharded reference tables and authentication data.
- `ticket_locator(ticket_id, member_id, shard_idx, timestamps...)` is the central lookup table for ticket-id based admin operations.
- The coordinator also owns `ticket_id_allocator`, which issues all new live `ticket_id` values globally.
- Cross-shard foreign keys are not used for sharded tickets.
- Ticket write validation is performed in application logic against coordinator tables before inserts and admin updates.

## API Routing Rules

- `POST /tickets`
  - derives `member_id` from the authenticated user
  - validates member/location/category/status against coordinator tables
  - allocates a globally unique `ticket_id` from the coordinator
  - inserts into the shard given by `(member_id - 1) % 3`
  - writes `ticket_locator`
  - compensates by deleting the just-inserted shard row if locator insert fails
- `GET /tickets`
  - queries exactly one shard using authenticated `member_id`
- `PUT /tickets/<ticket_id>`
  - resolves shard from `ticket_locator`
  - updates only that shard
- `DELETE /tickets/<ticket_id>`
  - resolves shard from `ticket_locator`
  - deletes from that shard and then deletes the locator row
- `GET /admin/tickets`
  - scatter-gathers across all 3 ticket shards
  - merges results deterministically by `created_at DESC, ticket_id DESC`
  - supports optional filters:
    - `created_from`
    - `created_to`
    - `ticket_id_min`
    - `ticket_id_max`

## Audit / Tamper Handling

- Coordinator audit triggers now cover:
  - `member_portfolio`
  - `ticket_locator`
- Ticket audit triggers moved to shard-local trigger scripts so ticket writes are audited where the ticket row actually lives.
- `/admin/tamper-events` now aggregates suspicious `DIRECT_DB` events from:
  - the coordinator audit table
  - all 3 shard audit tables
- This keeps ticket tamper detection correct after sharding.

## Prerequisites

- Python 3.8+
- MySQL instances reachable on:
  - coordinator port `3306` by default
  - ticket shard ports `3307`, `3308`, `3309`
- The original Module A schema/data import file: `Track1_Assignment1_ModuleA.sql`

## Environment Configuration

Create `.env` inside `Assignment_2/Module_B` and set the coordinator plus shard connection details:

```bash
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=fixiit_db

TICKET_SHARD_0_DB_HOST=127.0.0.1
TICKET_SHARD_0_DB_PORT=3307
TICKET_SHARD_0_DB_USER=root
TICKET_SHARD_0_DB_PASSWORD=your_mysql_password
TICKET_SHARD_0_DB_NAME=fixiit_ticket_shard_0

TICKET_SHARD_1_DB_HOST=127.0.0.1
TICKET_SHARD_1_DB_PORT=3308
TICKET_SHARD_1_DB_USER=root
TICKET_SHARD_1_DB_PASSWORD=your_mysql_password
TICKET_SHARD_1_DB_NAME=fixiit_ticket_shard_1

TICKET_SHARD_2_DB_HOST=127.0.0.1
TICKET_SHARD_2_DB_PORT=3309
TICKET_SHARD_2_DB_USER=root
TICKET_SHARD_2_DB_PASSWORD=your_mysql_password
TICKET_SHARD_2_DB_NAME=fixiit_ticket_shard_2

# Optional legacy source override for migration.
LEGACY_TICKET_SOURCE_DB_HOST=127.0.0.1
LEGACY_TICKET_SOURCE_DB_PORT=3306
LEGACY_TICKET_SOURCE_DB_USER=root
LEGACY_TICKET_SOURCE_DB_PASSWORD=your_mysql_password
LEGACY_TICKET_SOURCE_DB_NAME=fixiit_db
```

The migration script first reads from the legacy monolithic `tickets` table if available. If that table is unavailable, it falls back to the checked-in ticket seed section inside `Track1_Assignment1_ModuleA.sql`.

## Setup and Migration

### 1. Install dependencies

```bash
cd /Users/arinmehta/Documents/GitHub/FixIIT/Assignment_2/Module_B
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 2. Import the original coordinator schema/data

```bash
cd /Users/arinmehta/Documents/GitHub/FixIIT
mysql -h 127.0.0.1 -P 3306 -u root -p < Track1_Assignment1_ModuleA.sql
```

This creates the original unsharded coordinator schema and provides the monolithic `tickets` source data used for migration.

### 3. Create coordinator Module B tables and all ticket shard tables

```bash
cd /Users/arinmehta/Documents/GitHub/FixIIT/Assignment_2/Module_B
source myenv/bin/activate
python3 scripts/setup_sharded_databases.py
```

This script:

- creates the coordinator `Credentials`, `member_portfolio`, `ticket_locator`, and audit tables
- inserts Module B sample credentials/profile data
- installs coordinator audit triggers
- creates shard-local `tickets` and audit tables on ports `3307`, `3308`, `3309`
- installs shard-local ticket audit triggers

### 4. Migrate monolithic tickets into shards

```bash
cd /Users/arinmehta/Documents/GitHub/FixIIT/Assignment_2/Module_B
source myenv/bin/activate
python3 scripts/migrate_tickets_to_shards.py
```

This migration:

- preserves `ticket_id`
- computes target shard from `member_id`
- inserts into the correct shard
- writes `ticket_locator`
- detects `ticket_id` conflicts on the wrong shard and aborts clearly
- advances the coordinator `ticket_id_allocator` to `MAX(migrated ticket_id) + 1`

### 5. Run the Flask app

```bash
cd /Users/arinmehta/Documents/GitHub/FixIIT/Assignment_2/Module_B
source myenv/bin/activate
python3 run.py
```

## Verification

Run the included verification script after migration:

```bash
cd /Users/arinmehta/Documents/GitHub/FixIIT/Assignment_2/Module_B
source myenv/bin/activate
python3 scripts/verify_ticket_shards.py
```

The script checks:

- total source ticket count equals total tickets across all shards
- no duplicate `ticket_id` exists across shards
- every ticket is on the shard defined by `(member_id - 1) % 3`
- all tickets for one member are on one shard
- `GET /tickets` stays single-shard logically
- admin update/delete resolve the shard through `ticket_locator`
- `GET /admin/tickets` range filters merge cross-shard rows correctly

## Useful Manual API Checks

### Login

```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Member ticket read

```bash
curl -X GET http://127.0.0.1:5000/tickets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Ticket creation

```bash
curl -X POST http://127.0.0.1:5000/tickets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"AC issue",
    "description":"AC not cooling",
    "location_id":1,
    "category_id":3,
    "priority":"High"
  }'
```

### Cross-shard admin listing with filters

```bash
curl -X GET "http://127.0.0.1:5000/admin/tickets?created_from=2026-01-15&created_to=2026-01-17&ticket_id_min=3&ticket_id_max=15" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Tamper-event aggregation

```bash
curl -X GET http://127.0.0.1:5000/admin/tamper-events \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Demo Credentials

- Admin
  - username: `admin`
  - password: `admin123`
- User
  - username: `user`
  - password: `user123`

## Files Added for Sharding

- `app/sharding.py`
- `app/ticket_source.py`
- `sql/create_ticket_shard_tables.sql`
- `sql/create_ticket_shard_audit_triggers.sql`
- `scripts/setup_sharded_databases.py`
- `scripts/migrate_tickets_to_shards.py`
- `scripts/verify_ticket_shards.py`

## Limitations and Trade-offs

### Horizontal vs vertical scaling

- Ticket write/read load now scales horizontally across 3 ticket shards.
- Unsharded coordinator tables still scale vertically because they remain centralized.

### Consistency

- Ticket writes are split between a shard row and a coordinator `ticket_locator` row.
- The implementation uses explicit compensation on `POST /tickets` if locator insert fails after the shard insert.
- There is no distributed transaction manager; this is intentionally kept simple for coursework.

### Availability

- Coordinator availability remains critical because authentication, reference validation, RBAC, and `ticket_locator` all depend on it.
- Ticket shard availability affects only the members routed to that shard plus cross-shard admin ticket views.

### Partition tolerance

- A network partition between the app and any ticket shard will block ticket operations for members mapped to that shard.
- A coordinator partition blocks all authenticated ticket operations because validation and locator resolution depend on the coordinator.

### Why app-level validation replaced ticket foreign keys

- Shard-local `tickets` rows cannot safely retain foreign keys to coordinator tables across separate MySQL instances.
- The backend therefore validates `member_id`, `location_id`, `category_id`, and `status_id` in application logic before ticket writes.
- This preserves correctness for the coursework design without introducing cross-database foreign-key coupling.
