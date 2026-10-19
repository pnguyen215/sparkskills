---
name: database
description: 'Governs schema design, migrations, and query optimization — normalization, safe migration patterns, index strategy, and EXPLAIN-driven tuning. Trigger with "design this schema", "write the migration", "this query is slow", or "review this index".'
---

# Database

## Purpose

Keep data layers correct and fast: normalized, constraint-enforced schemas;
forward-only, backwards-compatible migrations; and queries justified by execution
plans instead of guesses. The skill covers relational work primarily (PostgreSQL
dialect) with the same rules mapping to MySQL and document stores' structured use.

## When to Use / When NOT to Use

Use when:

- Designing a new schema or evolving an existing one ("design this schema",
  "write the migration").
- A query is slow and needs EXPLAIN-driven tuning ("this query is slow").
- Choosing indexes, keys, or transaction isolation for a feature.

Do NOT use when:

- The problem is application-level query construction (N+1 from the ORM) — fix
  it there, but verify with this skill's EXPLAIN method.
- Caching strategy is the actual question — `observability` metrics plus
  architecture review own that; this skill owns the database itself.

## Prerequisites & Assumptions

- PostgreSQL 17+ (or MySQL 8.4+); migrations run by a versioned tool
  (golang-migrate, Flyway, Alembic, Atlas).
- Every migration is reviewed like code and tested against a staging-sized
  dataset before prod.
- Production schema changes go through the migration tool, never a manual SQL
  session.

## Step-by-Step Workflow

1. **Model the domain** — identify entities, relationships, and cardinality;
   normalize to 3NF by default; denormalize only with a measured read-path
   justification.
2. **Enforce integrity in the database** — primary keys, foreign keys, `NOT
NULL`, `CHECK`, and `UNIQUE` constraints; the application never is the only
   guard.
3. **Write migrations expand/contract** — phase 1 add nullable columns/new
   tables (expand), phase 2 backfill in batches, phase 3 switch reads/writes,
   phase 4 drop old structures (contract). Never one destructive step.
4. **Index from queries, not guesses** — after schemas exist, write the top
   queries, run `EXPLAIN (ANALYZE, BUFFERS)`, add the minimum indexes that turn
   scans into index scans for those plans.
5. **Tune the outlier** — for slow queries: read the plan (seq scan on large
   table? nested loop over millions? sort spilling to disk?), fix the plan cause
   (index, statistics, rewrite, limit), re-measure.
6. **Verify migrations** — test on a copy of prod-scale data, measure lock
   duration, confirm rollback/abort path for every migration.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** keep every migration forward-compatible (expand → migrate → contract);
  destructive changes require the old column to be dead for at least one release
  first.
- **MUST** wrap backfills in batches (e.g. 10k rows per transaction) and make
  them resumable; long transactions and table locks are release blockers.
- **MUST** enforce integrity with database constraints; `NOT NULL` on all
  required columns (add as `NULL`, backfill, then `SET NOT NULL`).
- **MUST** use parameterized queries in application code (see `security` for the
  injection rules).
- **MUST** justify every index with a query plan; each index costs write
  throughput and storage.
- **SHOULD** use UUIDv7 or similar time-ordered identifiers for high-write
  tables; integer sequences are fine for single-node internal systems.
- **SHOULD** set explicit transaction isolation for multi-statement money/state
  operations (`SELECT ... FOR UPDATE` where contention demands it).
- **MUST NOT** use `SELECT *` in application code.
- **MUST NOT** run manual DDL on production; every change is a reviewed
  migration file.
- **MUST NOT** store secrets or PII without the rules in `security` (encryption,
  redaction in logs).

## Examples

Good — expand/contract migration (PostgreSQL):

```sql
-- 001_add_order_tax.sql (expand: nullable + default, no lock pain)
ALTER TABLE orders ADD COLUMN tax_cents bigint;

-- 002_backfill_tax.sql (batched, resumable)
UPDATE orders SET tax_cents = 0
 WHERE tax_cents IS NULL
   AND id IN (SELECT id FROM orders WHERE tax_cents IS NULL LIMIT 10000);

-- 003_tax_not_null.sql (contract: enforce after backfill verified)
ALTER TABLE orders ALTER COLUMN tax_cents SET NOT NULL;
```

Bad — the big-bang destructive migration:

```sql
ALTER TABLE orders RENAME COLUMN total TO total_cents;  -- blocks writes,
-- breaks every running deploy reading `total`, no rollback path.
```

Why it fails: takes an exclusive lock, breaks the previous version of the
service mid-deploy, and cannot be aborted safely.

Good — EXPLAIN-driven index (PostgreSQL):

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status FROM orders WHERE user_id = 'u-1' AND status = 'open';
-- Seq Scan on orders (rows removed by filter: 4_982_113)  ← the smell
CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders (user_id, status);
-- Index Only Scan ... rows=12  ← the fix, verified
```

## Checklist

- [ ] Schema is 3NF unless a measured denormalization is documented.
- [ ] Constraints (PK/FK/NOT NULL/CHECK/UNIQUE) enforced in the database.
- [ ] Migrations are expand/contract, batched, resumable, and tested at
      prod scale.
- [ ] Every index justified by an `EXPLAIN (ANALYZE)` plan.
- [ ] No `SELECT *` in application queries; all queries parameterized.
- [ ] Transaction boundaries and isolation set for multi-step state changes.
- [ ] Rollback/abort path documented for each migration.

## Common Pitfalls

- **N+1 queries** — one query per item in a loop; batch with `IN`/joins and
  verify by plan.
- **Index everything** — write-heavy tables drown in index maintenance; index
  the proven top queries only.
- **Locking migrations at peak** — `ALTER TABLE` on a hot table without
  `CONCURRENTLY`/lock-timeout planning; schedule and use lock timeouts.
- **Implicit casts hiding scans** — comparing `text` to `uuid` silently drops
  the index; match column types exactly.

## References

- PostgreSQL documentation — indexes and EXPLAIN: https://www.postgresql.org/docs/current/using-explain.html
- PostgreSQL ALTER TABLE locking notes: https://www.postgresql.org/docs/current/sql-altertable.html
- Flyway migration best practices: https://documentation.red-gate.com/fd/best-practices-184127404.html
- Atlas (schema-as-code): https://atlasgo.io/
