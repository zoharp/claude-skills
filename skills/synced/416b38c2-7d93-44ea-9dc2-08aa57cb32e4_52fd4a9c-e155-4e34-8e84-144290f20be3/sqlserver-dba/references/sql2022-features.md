# SQL Server 2022 (v16, compat level 160)

Most of the performance features below require **compatibility level 160**, which is not set
automatically when a database is restored or attached from an older instance. A database running at
compat 130 on a 2022 instance gets almost none of this. Check first:

```sql
SELECT name, compatibility_level FROM sys.databases ORDER BY name;
```

## Intelligent Query Processing added in 2022

These adapt plans based on observed behavior rather than requiring code changes - which makes them
especially valuable for vendor or ORM-generated SQL you cannot edit.

**Parameter Sensitive Plan (PSP) optimization.** Caches multiple plans for a single parameterized
statement, dispatching by predicate cardinality range. This is the built-in answer to the classic
parameter sniffing problem for equality predicates on skewed columns, and it is the first thing to
try before reaching for `RECOMPILE` or plan forcing. It handles up to three predicates and applies
only where the optimizer detects significant skew, so it is not universal - verify with the actual
plan, which shows the dispatcher.

**Cardinality Estimation (CE) feedback.** Identifies repeating queries whose CE model assumptions
(correlation, independence, containment) produce bad estimates and tries alternative models,
persisting what works via Query Store. This helps the long tail of queries that regressed on the
new CE introduced in 2014.

**Degree of Parallelism (DOP) feedback.** Detects queries where parallelism hurts - typically high
`CXPACKET` with no elapsed-time benefit - and lowers DOP for that query, persisting the decision.
Requires Query Store to be enabled and read-write.

**Memory Grant Feedback persistence and percentile mode.** 2017/2019 memory grant feedback was lost
on restart or recompile; 2022 persists it in Query Store and uses a percentile of recent grants
rather than the last execution, which stops it oscillating on workloads with genuinely varying row
counts.

Blanket disable of any of these is available at database scope
(`ALTER DATABASE SCOPED CONFIGURATION SET ...`) if one causes a regression - useful to know when
triaging a post-upgrade problem.

## Query Store changes

- **On by default for newly created databases**, in read-write mode.
- **Query Store for secondary replicas** - collects statistics from readable AG secondaries into the
  primary's Query Store, so read-scale workloads are finally tunable.
- **Query Store hints** (introduced 2019, extended here) remain the best way to shape a plan without
  touching application code: `EXEC sys.sp_query_store_set_hints @query_id, N'OPTION(RECOMPILE)'`.

## Engine and concurrency improvements

Free with the upgrade, no code changes:

- **System page latch concurrency** improvements for GAM/SGAM/PFS pages, which reduces allocation
  contention on heavy-insert workloads and in tempdb.
- **tempdb system table concurrency** - the memory-optimized tempdb metadata option from 2019 is
  extended, reducing the classic `PAGELATCH` metadata bottleneck.
- **Buffer pool parallel scan**, which shortens operations that had to walk the buffer pool (drop
  database, some DDL) on very large-memory instances.
- **Improved parallel redo** for AG secondaries.

## Availability, backup and platform

- **Contained availability groups** carry their own `master` and `msdb`, so logins, jobs and
  permissions fail over with the group - a long-standing operational pain point resolved.
- **Backup and restore to S3-compatible object storage** via `BACKUP ... TO URL`, alongside the
  existing Azure Blob support. Relevant for AWS-hosted instances that previously needed a file share.
- **Link feature for Azure SQL Managed Instance** - near-real-time replication to a managed instance
  for DR or migration.
- Multi-write replication and enhanced snapshot backup support (`ALTER SERVER CONFIGURATION SET
  SUSPEND_FOR_SNAPSHOT_BACKUP`).

## Security and compliance

- **Ledger tables** - blockchain-style, cryptographically verifiable history. Updatable ledger tables
  keep an append-only history table plus a database digest that can be stored externally
  (immutable Azure storage or the like) so tampering is detectable even by someone with `sysadmin`.
  For regulated environments this is the strongest available answer to "prove the audit trail was
  not altered", and worth proposing wherever a hand-rolled audit-trigger scheme is being designed.
- Integrated authentication with Azure AD (Microsoft Entra ID).
- Always Encrypted with secure enclaves supports more operations, including `LIKE` and range
  comparisons on encrypted columns.
- Dynamic data masking granularity improvements.

## T-SQL added in 2022

Small but they remove a lot of legacy workaround code:

```sql
SELECT GREATEST(a, b, c), LEAST(a, b, c) FROM t;      -- no more CASE ladders or VALUES tricks
SELECT value, ordinal FROM STRING_SPLIT('a,b,c', ',', 1);   -- split order finally available
SELECT DATE_BUCKET(week, 1, OrderDate);               -- clean time bucketing for reporting
SELECT * FROM GENERATE_SERIES(1, 100, 1);             -- numbers table without a helper table
SELECT * FROM t WHERE Col IS DISTINCT FROM @p;        -- NULL-safe comparison, no ISNULL
SELECT DATETRUNC(month, OrderDate);
SELECT SUM(x) OVER w, AVG(x) OVER w                   -- named WINDOW clause, no repetition
FROM t WINDOW w AS (PARTITION BY g ORDER BY d);
SELECT LEFT_SHIFT(@v, 2), BIT_COUNT(@v);              -- bit manipulation functions
SELECT APPROX_PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x) FROM t;  -- fast approximate percentiles
```

`IS DISTINCT FROM` is directly useful in trigger change-detection logic, replacing the
`EXCEPT`-based idiom.

Also added: XML compression, auto-drop statistics, and improvements to `JSON` handling
(with far larger JSON changes arriving in later versions).

## Upgrade approach

The optimizer changes are where upgrades go wrong. A safe sequence:

1. Upgrade the instance, leaving each database at its **existing** compatibility level. The engine
   is new; the query optimizer behavior is unchanged.
2. Enable Query Store and collect a representative baseline - at minimum a full business cycle
   including month-end.
3. Raise compatibility level to 160 on one database.
4. Use the Query Store **Regressed Queries** view to find what got worse. Force the previous plan
   for anything material, then fix the underlying cause and unforce.
5. Only then evaluate the new IQP features individually if you disabled any.

`ALTER DATABASE SCOPED CONFIGURATION SET LEGACY_CARDINALITY_ESTIMATION = ON` lets a database use the
new engine with the old (pre-2014) estimator - a blunt instrument, but useful when a legacy
application regresses broadly and there is no time to tune individual queries.

## Version quick reference

| Version | Compat | Notable for tuning |
|---|---|---|
| 2016 (13) | 130 | Query Store, new CE default, tempdb autoconfiguration, most Enterprise features into Standard at SP1 |
| 2017 (14) | 140 | Adaptive joins, interleaved execution, memory grant feedback |
| 2019 (15) | 150 | Scalar UDF inlining, table variable deferred compilation, memory-optimized tempdb metadata, `OPTIMIZE_FOR_SEQUENTIAL_KEY`, Query Store hints, resumable index create |
| 2022 (16) | 160 | PSP optimization, CE feedback, DOP feedback, persisted memory grant feedback, ledger tables, contained AGs, S3 backup |

Mainstream support for SQL Server 2016 has ended and extended support ends in July 2026 - worth
raising if the user is running it.
