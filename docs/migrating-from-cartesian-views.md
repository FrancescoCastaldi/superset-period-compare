# Migrating from Cartesian SQL Views to Period Compare

This guide shows how to retire the old database views with self joins or Cartesian products that were used to compare historical periods, and replace them with the native, high performance approach of Superset Period Compare.

## 1. The problem with traditional SQL views

To compare time periods in Superset, many teams built SQL views like this:

```sql
/* OLD APPROACH (PROBLEMATIC): */
SELECT
    t1.id,
    t1.event_date AS reference_date,
    t1.value AS reference_value,
    t2.value AS comparison_value,
    (t1.value - t2.value) AS difference
FROM events t1
LEFT JOIN events t2
    ON t2.category = t1.category
    AND t2.event_date = DATEADD(month, -1, t1.event_date);
```

Drawbacks of the old approach:

1. **Rigidity.** The comparison is fixed in the SQL (for example only the previous month). Comparing with a year ago, or two arbitrary windows, required duplicated views.
2. **Row explosion.** Self joins over millions of rows degrade database performance and slow down the dashboard.
3. **Hard maintenance.** Every change to a column or a metric meant editing and realigning the production views.

## 2. The native approach

With Superset Period Compare the dataset points directly at the **plain table** (or a clean view without temporal joins):

```sql
/* NEW APPROACH (SIMPLE, CLEAN AND FAST): */
SELECT
    id,
    event_date,
    category,
    value
FROM events;
```

All the comparison logic moves to the analytic engine of Superset:

1. The backend runs two separate, targeted aggregate queries: one on the reference period and one on the comparison period.
2. Each query filters only the relevant time ranges, making the best use of indexes and partitions in the database.
3. Alignment and the calculation of the difference or percentage change happen in memory, in the Superset analytic process.

## 3. Step by step migration checklist

1. **Create the plain dataset.** In Superset, create or select the dataset that points to the physical table or to a lean view.
2. **Add the native filter.** In the dashboard, create a new native filter of type `Period comparison filter`.
3. **Connect the charts.** Check that the charts of the dashboard have the `Follow dashboard comparison` option on (it is on by default).
4. **Validate the totals.** Check that the displayed values match the actual historical data.
5. **Retire the old view.** Remove the old SQL view or helper table from the database, recovering disk space and simplifying maintenance.
