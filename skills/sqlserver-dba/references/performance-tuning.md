# Performance tuning

Contents: [Wait types](#wait-types-and-what-they-mean) · [Query Store](#query-store)
· [Reading plans](#reading-execution-plans) · [SARGability](#sargability-the-biggest-single-win)
· [Parameter sniffing](#parameter-sniffing) · [Statistics](#statistics)
· [Blocking](#blocking-and-isolation) · [Deadlocks](#deadlocks) · [tempdb and memory](#tempdb-and-memory-grants)
· [Anti-patterns](#recurring-anti-patterns)

## Wait types and what they mean

Wait statistics answer "what is SQL Server waiting on", which narrows the search from the whole
instance to one subsystem. `scripts/wait_stats.sql` returns them with the benign ones filtered out.
Remember `sys.dm_os_wait_stats` is cumulative since restart (or since
`DBCC SQLPERF('sys.dm_os_wait_stats', CLEAR)`), so a delta over a fixed window is far more useful
than the raw total.

| Wait | Usually means | First things to check |
|---|---|---|
| `CXPACKET` / `CXCONSUMER` | Parallelism. `CXCONSUMER` alone is often benign | Cost threshold for parallelism (raise from 5 to ~50), MAXDOP, skewed distribution from bad estimates |
| `PAGEIOLATCH_SH/EX` | Reading data pages from disk | Missing index causing scans, insufficient memory, slow storage. Tune the query first |
| `WRITELOG` | Transaction log write latency | Log file storage latency, too many small transactions, autogrowth events |
| `LCK_M_*` | Blocking | Long transactions, missing indexes forcing wide locks, isolation level, lock escalation |
| `PAGELATCH_UP/EX` on 2:x:x | tempdb allocation contention | Number and equal sizing of tempdb data files; 2019+ memory-optimized tempdb metadata |
| `RESOURCE_SEMAPHORE` | Queries queuing for memory grants | Oversized grants from bad estimates, missing indexes causing sorts/hashes, max server memory |
| `SOS_SCHEDULER_YIELD` | CPU pressure | High-CPU queries, excessive parallelism, spinlock contention |
| `THREADPOOL` | Worker thread exhaustion | Severe blocking chain; often a symptom, not the cause |
| `ASYNC_NETWORK_IO` | Client not consuming results fast enough | Application pulling too many rows, row-by-row client processing |
| `HADR_SYNC_COMMIT` | Synchronous AG replica commit latency | Replica health, network latency between replicas |
| `RESOURCE_GOVERNOR_IDLE`, `SLEEP_*`, `XE_*`, `BROKER_*` | Background noise | Filter out |

## Query Store

Query Store is the single most useful tuning feature added since 2016 and is on by default for new
databases in 2022. It persists plans, runtime statistics and wait categories per query, surviving
restarts and plan cache eviction.

Recommended settings for a busy OLTP database:

```sql
ALTER DATABASE [YourDb] SET QUERY_STORE = ON
    (OPERATION_MODE = READ_WRITE,
     QUERY_CAPTURE_MODE = AUTO,              -- skips trivial one-off queries
     MAX_STORAGE_SIZE_MB = 2048,
     DATA_FLUSH_INTERVAL_SECONDS = 900,
     INTERVAL_LENGTH_MINUTES = 30,           -- 60 is the default; 30 gives finer regression detection
     SIZE_BASED_CLEANUP_MODE = AUTO,
     STALE_QUERY_THRESHOLD_DAYS = 30,
     WAIT_STATS_CAPTURE_MODE = ON);
```

Uses that matter:

- **Regression hunting.** Compare a query's plans before and after a release or a statistics
  update; the built-in "Regressed Queries" report does this directly.
- **Plan forcing.** `sp_query_store_force_plan` pins a known-good plan. Treat it as a temporary
  splint, not a fix - forced plans can become invalid after schema changes and stop being honored
  silently. Track every forced plan and revisit it.
- **Query Store hints (2019+).** `sp_query_store_set_hints` applies a hint to a query without
  touching application code - the modern replacement for plan guides:
  ```sql
  EXEC sys.sp_query_store_set_hints @query_id = 1234,
       @query_hints = N'OPTION(RECOMPILE, MAXDOP 1)';
  ```
  Invaluable when the SQL is embedded in a vendor application or an ORM.
- **Safe compatibility-level upgrades.** Enable Query Store, collect a baseline on the old compat
  level, raise the level, then compare and force plans for anything that regressed.

## Reading execution plans

Always get the **actual** plan (`SET STATISTICS XML ON`, or "Include Actual Execution Plan"). Read
it in this order:

1. **Estimated vs actual rows.** A gap over roughly 10x is the root cause of most bad plans - the
   optimizer sized memory, join type and index choice for the wrong data volume. Trace it back to
   the operator where the gap first appears; that is where the estimate broke (stale statistics, a
   table variable, a multi-statement TVF, a non-SARGable predicate, a local variable).
2. **Warnings** on operators - implicit conversion, no join predicate, spills to tempdb, excessive
   memory grant. These are free diagnoses; the plan is telling you the answer.
3. **Scan vs seek in context.** A scan of a 200-row lookup table is fine. A scan of a 50M-row table
   to return 3 rows is not. Seek plus a large key lookup count can be worse than a scan - that is
   the covering-index signal.
4. **Join types.** Nested loops with a large outer input, or a hash join where a merge or loop was
   expected, usually points back to item 1 rather than being a problem in itself.
5. **Blocking operators** - sorts, hash aggregates, spools. Eager spools frequently indicate a
   Halloween-protection issue or a missing index on a modification.
6. **Cost percentages are estimates**, including in actual plans. Use them to navigate, never as
   proof. `SET STATISTICS IO, TIME ON` gives real logical reads and CPU.

The metric to optimize is usually **logical reads**, because it is stable across cache states and
hardware, unlike duration.

## SARGability: the biggest single win

A predicate is SARGable when the engine can use it to seek. Wrapping a column in anything destroys
that.

| Instead of | Write |
|---|---|
| `WHERE YEAR(OrderDate) = 2024` | `WHERE OrderDate >= '20240101' AND OrderDate < '20250101'` |
| `WHERE CAST(OrderDate AS date) = @d` | `WHERE OrderDate >= @d AND OrderDate < DATEADD(day,1,@d)` |
| `WHERE ISNULL(Status,'') = 'X'` | `WHERE Status = 'X'` (add `OR Status IS NULL` if needed) |
| `WHERE LEFT(Code,3) = 'ABC'` | `WHERE Code LIKE 'ABC%'` |
| `WHERE Code LIKE '%ABC%'` | Full-text index, or a computed persisted column |
| `WHERE Total * 1.1 > @x` | `WHERE Total > @x / 1.1` |
| `WHERE @p IS NULL OR Col = @p` | Split into branches, or add `OPTION(RECOMPILE)` |

**Implicit conversion** is the sneaky version: an `nvarchar` parameter compared against a `varchar`
column forces `CONVERT_IMPLICIT` on every row and kills the seek. It is common with ORMs, which
default to Unicode parameters. Fix the parameter type or the column type - the plan warning names
the column.

## Parameter sniffing

SQL Server compiles a plan for the parameter values of the *first* execution and reuses it. When
data is skewed - one customer with 5 million orders, the rest with ten - one plan is wrong for
somebody. Symptoms: a procedure that is fast for weeks then suddenly slow for everyone after a
restart or statistics update, while the same SQL run ad hoc is fast.

Options, cheapest first:

- **Fix the estimate.** Better indexes and statistics often remove the sensitivity entirely.
- **SQL Server 2022 Parameter Sensitive Plan optimization** caches multiple plans for different
  predicate cardinality ranges automatically. Requires compat level 160. Check whether this
  resolves it before adding hints.
- `OPTION (RECOMPILE)` - a fresh optimal plan every time, at the cost of compile CPU on every
  execution. Excellent for reports run occasionally, terrible for a procedure called 1,000 times a
  second.
- `OPTION (OPTIMIZE FOR (@p = 'typical value'))` when one value represents the common case;
  `OPTIMIZE FOR UNKNOWN` uses the density vector average - mediocre for everyone but stable.
- **Split the procedure** into branches that call separate sub-procedures, each compiling its own
  plan for its own shape of data. Verbose but the most controllable.
- Query Store plan forcing as a stopgap while a real fix is developed.

Do **not** "fix" it by copying parameters into local variables. That defeats sniffing by making
every estimate a density guess, which frequently produces a worse plan that is now consistently
bad instead of intermittently bad.

## Statistics

- Auto-update fires at roughly 20% of rows changed on older thresholds; 2016+ with compat 130+ uses
  a sqrt-based dynamic threshold that triggers much more often on large tables. Verify compat level
  before assuming.
- **Ascending key problem**: rows inserted today fall outside the histogram's last step, so queries
  for recent data estimate one row. Watch for it on any `datetime`/identity-filtered query. Remedy:
  more frequent stats updates on that table, or trace flag 2371 behavior (default on 2016+).
- Sampling matters. `UPDATE STATISTICS tbl WITH FULLSCAN` on the tables that drive bad estimates;
  auto-update's default sample can be under 1% on huge tables. 2016 SP1+ supports
  `WITH PERSIST_SAMPLE_PERCENT = ON` so later auto-updates keep your chosen rate.
- **Index rebuilds update statistics with fullscan; reorganizes do not.** A maintenance job that
  switched from rebuild to reorganize is a classic cause of overnight regressions.
- Filtered statistics help when a table holds heterogeneous subsets (a status column with wildly
  different distributions).
- `DBCC SHOW_STATISTICS('dbo.Table','IX_Name')` shows the histogram; `sys.dm_db_stats_properties`
  reports last update time and modification counter across all statistics.

## Blocking and isolation

Blocking is normal; *sustained* blocking is a bug. Use `scripts/blocking_and_deadlocks.sql` to see
the live chain and the head blocker.

Root causes in order of frequency: transactions that stay open across application round trips or
user think-time; missing indexes forcing a modification to scan and lock far more rows than it
changes; lock escalation to table level once a statement touches around 5,000 locks; explicit
`SERIALIZABLE`/`REPEATABLE READ` where it was not needed.

**`READ_COMMITTED_SNAPSHOT` is usually the right answer for OLTP read blocking**:

```sql
ALTER DATABASE [YourDb] SET READ_COMMITTED_SNAPSHOT ON WITH ROLLBACK IMMEDIATE;
```

Readers stop blocking writers by reading a row version. The costs are real and must be stated:
tempdb version store growth, 14 extra bytes per row as rows are updated, and different application
semantics for read-then-update patterns (which need `UPDLOCK` hints or optimistic concurrency
checks). It also requires exclusive database access for the moment of the switch.

`WITH (NOLOCK)` is not an alternative. It permits dirty reads, rows read twice, and rows skipped
entirely during page splits - in a regulated system that is a data-integrity finding, not an
optimization.

## Deadlocks

Deadlock graphs are already being captured - the `system_health` Extended Events session retains
them by default, and `scripts/blocking_and_deadlocks.sql` extracts them without any setup.

Reading a graph: identify the two (or more) resources, the lock modes, and crucially the
**statement each process was running**. The pattern is almost always inconsistent access order -
process A updates Orders then OrderLines, process B does the reverse.

Fixes, in order: make all code paths touch tables in the same order; shorten transactions; add
indexes so modifications lock fewer rows (a huge share of "deadlocks" are really two scans
colliding); consider RCSI to remove read-write conflicts. As a last resort adjust
`DEADLOCK_PRIORITY` to choose the victim deliberately.

Regardless of the fix, **the application must retry deadlock victims** (error 1205). Deadlocks can
never be fully eliminated in a concurrent system; a retry with a small backoff is standard practice
and belongs in the data access layer.

## tempdb and memory grants

- Memory grants are sized from estimated rows and row width. A bad estimate causes either a spill
  to tempdb (grant too small - visible as a warning in the actual plan) or grant hoarding that
  produces `RESOURCE_SEMAPHORE` waits for everyone else (grant too large).
- 2017+ Memory Grant Feedback corrects repeat offenders automatically; 2022 persists that feedback
  across restarts in Query Store and adds percentile-based feedback for varying workloads.
- Spills at the Sort or Hash Match operators are a direct signal to fix estimates or add a
  supporting index rather than to add memory.
- tempdb sizing and contention are covered in `references/config-and-maintenance.md`.

## Recurring anti-patterns

- **Scalar UDFs** in `SELECT` lists or `WHERE` clauses: historically executed per row and forced
  serial plans. 2019+ can inline many of them (compat 150+), but not all - check
  `sys.sql_modules.is_inlineable`. Rewrite as inline table-valued functions where possible.
- **Multi-statement TVFs** estimated at 100 rows (1 row before 2014, 100 with interleaved execution
  on 2017+), wrecking downstream joins.
- **Table variables** have no statistics and estimate 1 row, though 2019+ deferred compilation
  helps at compat 150+. Use `#temp` tables for anything with meaningful row counts.
- **`SELECT *`** prevents covering indexes from ever covering, and inflates network and memory grants.
- **Cursors and `WHILE` loops** where a set-based statement works.
- **Nested views** several layers deep - the optimizer sees the expanded tree and often gives up.
- **`ORDER BY` on huge result sets** the application then pages through in the client.
- **Over-indexing.** Every index is maintained on every write and consumes buffer pool. Consolidate
  duplicates rather than accumulating one index per query.
