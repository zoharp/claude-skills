# Triggers in SQL Server

Contents: [Decide first](#decide-whether-a-trigger-is-right) · [Correctness rules](#the-correctness-rules)
· [Template](#template-for-an-after-trigger) · [Transactions and errors](#transactions-and-error-handling)
· [INSTEAD OF](#instead-of-triggers) · [Order, nesting, recursion](#ordering-nesting-and-recursion)
· [Performance](#performance) · [DDL and logon triggers](#ddl-and-logon-triggers) · [Audit trails](#audit-trail-architecture)
· [Debugging](#debugging-and-inventory) · [Review checklist](#review-checklist)

## Decide whether a trigger is right

Triggers are invisible at the call site: someone runs an `UPDATE`, and code they cannot see runs
inside their transaction. That is exactly why they are useful for audit and exactly why they are a
poor default. Check the alternatives first.

| Goal | Prefer | Trigger only when |
|---|---|---|
| Audit history of row changes | System-versioned temporal tables | You need the *who*/*why*, not just the what and when (temporal records no user context) |
| Tamper-evident audit (21 CFR Part 11, SOX) | Ledger tables (2022) | Pre-2022, or the schema cannot be ledger-enabled |
| Feed changes downstream | Change Data Capture / Change Tracking | The consumer must see changes synchronously |
| Enforce a rule about one row | `CHECK` constraint | The rule spans rows or tables |
| Enforce referential integrity | `FOREIGN KEY` | Cross-database or conditional references |
| Derived column | Computed column (persisted if indexed) | The value depends on other tables |
| Denormalized rollup | Indexed view | The view restrictions block it |

If a trigger really is the answer, say so plainly and then make it correct.

## The correctness rules

**1. Triggers fire once per statement.** `inserted` and `deleted` are result sets that may hold
zero, one, or a million rows. Any assignment like `SELECT @CustomerId = CustomerId FROM inserted`
grabs an arbitrary row and silently corrupts data on multi-row DML. This is the number one trigger
bug in the wild, and single-row testing never catches it. Write joins, not variable assignments.

**2. Handle the zero-row case.** An `UPDATE` matching nothing still fires the trigger. Exit early:

```sql
IF ROWCOUNT_BIG() = 0 RETURN;
```

**3. Know your virtual tables.** `INSERT` populates `inserted`; `DELETE` populates `deleted`;
`UPDATE` populates both, joined on the primary key. There is no `updated` table. These are not
indexed, so on large batches materializing them into a `#temp` with an index before joining can be
faster than repeated scans.

**4. `TRUNCATE TABLE` does not fire `DELETE` triggers.** Neither does `bcp` or `BULK INSERT`
unless `FIRE_TRIGGERS` is specified, nor writes that bypass the engine. Never claim a trigger
guarantees a complete audit trail without also blocking those paths (deny permissions, or use
ledger/temporal).

**5. Detect column changes properly.** `UPDATE(ColumnName)` returns true when the column was
*referenced* by the statement, not when the value actually changed. To catch real changes, compare:

```sql
FROM inserted i
JOIN deleted d ON d.OrderId = i.OrderId
WHERE EXISTS (SELECT i.Status EXCEPT SELECT d.Status)   -- NULL-safe change detection
```

The `EXCEPT` idiom handles `NULL` correctly, unlike `i.Status <> d.Status`. On 2022 you can use
`IS DISTINCT FROM` instead.

## Template for an AFTER trigger

```sql
CREATE OR ALTER TRIGGER dbo.TR_Orders_Audit
    ON dbo.Orders
    AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;                 -- prevents extra rowcount messages breaking clients
    IF ROWCOUNT_BIG() = 0 RETURN;   -- no rows touched, nothing to do

    INSERT INTO dbo.OrderAudit (OrderId, Action, OldStatus, NewStatus,
                                ChangedBy, ChangedAtUtc, SessionContextUser)
    SELECT COALESCE(i.OrderId, d.OrderId),
           CASE WHEN i.OrderId IS NULL THEN 'DELETE'
                WHEN d.OrderId IS NULL THEN 'INSERT'
                ELSE 'UPDATE' END,
           d.Status,
           i.Status,
           SUSER_SNAME(),                                  -- login, not app user
           SYSUTCDATETIME(),
           CONVERT(sysname, SESSION_CONTEXT(N'AppUser'))   -- app-set identity, see below
    FROM inserted i
    FULL OUTER JOIN deleted d ON d.OrderId = i.OrderId;
END;
```

`FULL OUTER JOIN` lets one trigger body cover all three actions. If the application connects
through a shared service account, `SUSER_SNAME()` records only that account - have the application
call `sp_set_session_context N'AppUser', @user` after opening the connection so the trigger can
record the real end user. That distinction matters for any regulated audit trail.

## Transactions and error handling

A trigger executes inside the transaction of the statement that fired it. Consequences:

- Anything the trigger does is rolled back if the outer statement fails, and vice versa.
- Trigger duration is added to the lock-hold time of the original statement. Slow trigger equals
  application-wide blocking.
- `ROLLBACK TRANSACTION` inside a trigger rolls back the *entire* outer transaction and aborts the
  batch. Statements remaining in the trigger body after the rollback still execute, which surprises
  people. Avoid it.

To reject a change, throw instead:

```sql
IF EXISTS (SELECT 1 FROM inserted WHERE Quantity < 0)
    THROW 50001, 'Quantity cannot be negative.', 1;
```

With `SET XACT_ABORT ON` at the caller (or the default trigger behavior for most errors), the
transaction is doomed and rolled back cleanly, and the client gets a real error number it can
handle. Callers should check `XACT_STATE()` in their `CATCH` block before deciding to `ROLLBACK`
or `COMMIT`.

Note that `OUTPUT` results returned directly to the client are not supported on tables with
enabled triggers - `OUTPUT ... INTO` a table variable or temp table instead. Adding a trigger to a
table can therefore break an existing application in a way that is not obvious from the trigger
code.

## INSTEAD OF triggers

`INSTEAD OF` replaces the DML action; the original statement never runs unless the trigger performs
it. The two legitimate uses:

- **Making a multi-table view updatable.** The trigger decomposes the incoming rows into the base
  tables in the correct order.
- **Intercepting deletes for soft-delete semantics** - turn a `DELETE` into `UPDATE ... SET
  IsDeleted = 1`. Cleaner than an `AFTER` trigger that reinserts.

Constraints: one `INSTEAD OF` trigger per action per table or view; not allowed on a target of a
cascading `FOREIGN KEY` action for the same action; `AFTER` triggers cannot be defined on views at
all. Memory-optimized tables support only natively compiled `AFTER` triggers.

The classic bug: an `INSTEAD OF INSERT` trigger that forgets to perform the actual insert. The
statement reports success and writes nothing.

## Ordering, nesting and recursion

- Multiple `AFTER` triggers on the same action fire in unspecified order. `sp_settriggerorder` pins
  only the first and last. If order matters between three triggers, merge them - you cannot express
  the middle.
- **Nesting**: a trigger's DML fires other tables' triggers, up to 32 levels
  (`sys.configurations` option `nested triggers`, on by default). Exceeding the limit aborts the
  whole chain. `TRIGGER_NESTLEVEL()` reports current depth and is the standard way to make a
  trigger no-op when invoked from another trigger.
- **Direct recursion** (trigger updates its own table, re-firing itself) is controlled by the
  database option `RECURSIVE_TRIGGERS`, off by default. Indirect recursion (A fires B fires A) is
  governed by the nesting setting instead and is much easier to create accidentally.
- Write triggers to be idempotent where practical; retry logic and nesting both make double
  execution plausible.

## Performance

The cost of a trigger is paid by every DML statement on the table, forever.

- Keep the body to set-based statements. A cursor in a trigger multiplies its cost by row count.
- Index the audit target on the columns the trigger joins or filters on; an unindexed audit table
  turns into a scan per statement once it grows.
- Never call linked servers, `sp_send_dbmail`, `xp_cmdshell`, CLR web calls, or anything that waits
  on an external resource - the caller's locks are held for the whole duration.
- Bulk loads: `FIRE_TRIGGERS` off makes a load fast but leaves the audit incomplete. Decide
  deliberately and document it; for regulated systems, either fire the triggers or record the bulk
  operation separately.
- For very high-volume tables, consider disabling the trigger during a maintenance load
  (`DISABLE TRIGGER ... ON ...`) and back-filling the audit rows in one set-based statement - but
  only under a change control that guarantees re-enabling it. A permanently disabled trigger is a
  silent audit gap; `scripts/trigger_inventory.sql` flags them.
- Triggers block some optimizations, including certain minimally-logged bulk paths, which can turn
  a fast load into a fully-logged one.

## DDL and logon triggers

DDL triggers respond to schema events at database or server scope - useful for change control in
validated environments:

```sql
CREATE TRIGGER TR_DDL_SchemaAudit
    ON DATABASE
    FOR DDL_DATABASE_LEVEL_EVENTS
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @e xml = EVENTDATA();
    INSERT INTO dbo.SchemaChangeLog (EventType, ObjectName, LoginName, TSqlText, OccurredAtUtc)
    VALUES (@e.value('(/EVENT_INSTANCE/EventType)[1]',  'nvarchar(100)'),
            @e.value('(/EVENT_INSTANCE/ObjectName)[1]', 'nvarchar(255)'),
            @e.value('(/EVENT_INSTANCE/LoginName)[1]',  'nvarchar(255)'),
            @e.value('(/EVENT_INSTANCE/TSQLCommand/CommandText)[1]', 'nvarchar(max)'),
            SYSUTCDATETIME());
END;
```

Logon triggers fire on every connection at server scope. They can lock everyone out of the
instance if they error or run slowly - test with a dedicated admin connection open, and know that
the recovery path is starting SQL Server with the `-f` minimal configuration flag.

## Audit trail architecture

For regulated systems (21 CFR Part 11, Annex 11, SOX), a trigger-based audit trail is defensible
only if it is complete and tamper-evident. Practical layering:

1. **Ledger tables (2022)** for tamper evidence - cryptographically verifiable, and the strongest
   answer to "prove nobody edited the audit log".
2. **Temporal tables** for the full before/after row history with no custom code to validate.
3. **Triggers** for what the first two cannot capture: the acting application user, the reason for
   change, e-signature linkage.
4. **Permissions** so no one can `TRUNCATE`, disable triggers, or write to base tables directly -
   otherwise the audit trail has documented holes.

Record UTC (`SYSUTCDATETIME()`), keep the audit table append-only, and be able to demonstrate that
retention and access controls match the SOP.

## Debugging and inventory

```sql
-- what exists, and is any of it silently disabled?
SELECT OBJECT_SCHEMA_NAME(t.parent_id) AS parent_schema,
       OBJECT_NAME(t.parent_id)        AS parent_object,
       t.name, t.is_disabled, t.is_instead_of_trigger,
       te.type_desc                    AS fires_on,
       m.definition
FROM sys.triggers t
JOIN sys.trigger_events te ON te.object_id = t.object_id
JOIN sys.sql_modules   m   ON m.object_id  = t.object_id
WHERE t.parent_class = 1
ORDER BY parent_schema, parent_object, t.name;
```

Techniques that work when a trigger misbehaves:

- Reproduce with a **multi-row** DML statement. Most trigger bugs are invisible with one row.
- Capture the intent without side effects: temporarily write `inserted`/`deleted` to a scratch
  table, or wrap the test in `BEGIN TRAN ... ROLLBACK`.
- Get the actual execution plan of the DML statement - the trigger appears as a separate query plan
  under the statement, and expensive triggers hide there.
- Extended Events (`sql_statement_completed`, filtered on the object) shows real trigger cost;
  `sys.dm_exec_trigger_stats` gives cumulative execution counts and durations since restart.

## Review checklist

Run through this whenever reviewing or writing trigger code:

- [ ] Set-based - no scalar assignment from `inserted`/`deleted`, no cursor
- [ ] `SET NOCOUNT ON` and a zero-row early exit
- [ ] Correct virtual tables for the actions declared, `FULL OUTER JOIN` if it handles all three
- [ ] NULL-safe change detection (`EXCEPT` or `IS DISTINCT FROM`), not `<>`
- [ ] No `ROLLBACK` inside the trigger; `THROW` with a documented error number instead
- [ ] No external calls, no cursors, no unbounded loops
- [ ] Audit target indexed and append-only
- [ ] Records the real user, not just the service account
- [ ] Nesting/recursion behavior considered and documented
- [ ] Callers that rely on `OUTPUT` still work
- [ ] The bulk-load and `TRUNCATE` bypass paths are blocked or accounted for
