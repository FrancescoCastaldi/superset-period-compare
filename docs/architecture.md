# Technical Architecture: Superset Period Compare

This document describes the internals, the data flow and the architectural decisions behind the Period Compare module for Apache Superset 6.1.0. Individual decisions are recorded in [adr/](adr/README.md).

## 1. Architectural principles

1. **Reuse the native primitives.**
   Superset 6.1.0 already has a backend engine (`processing_time_offsets` in `helpers.py`) that handles explicit range offsets through the feature flag `DATE_RANGE_TIMESHIFTS_ENABLED`. The module extends this mechanism without introducing parallel engines, duplicated filters or Jinja templating logic.
2. **One to one temporal alignment.**
   The main limitation of upstream Superset was the lack of axis alignment for range offsets on time series: Superset dropped the secondary date column and produced null values (NaN). Period Compare shifts the date column of the comparison period by the exact granularity (whole months when the dates fall on the first day of a month, otherwise days), which allows a clean join on the time column of the reference period.
3. **Isolation and respect for user plugins.**
   No file under `superset-frontend/plugins/superset-plugin-*` is touched or overwritten. The only point of contact with the plugin registry is `MainPreset.ts`, which is changed only between the explicit markers `period-compare:begin` and `period-compare:end`.

## 2. Data flow

```
 +-------------------------------------------------------------------+
 | Dashboard UI (native PeriodCompare filter)                        |
 | The user selects:                                                 |
 |  - Reference period:  "2026-09-01 : 2026-10-01"                   |
 |  - Comparison preset: "Previous month" (or a free range)          |
 |  - Calculation mode:  "Actual values", "Difference", "%"          |
 +----------------------------------+--------------------------------+
                                    |
                                    v emits a dataMask (extraFormData)
 +-------------------------------------------------------------------+
 | extraFormData:                                                    |
 |   time_range:      "2026-09-01 : 2026-10-01"                      |
 |   time_compare:    ["2026-08-01 : 2026-09-01"]                    |
 |   comparison_type: "values"                                       |
 +----------------------------------+--------------------------------+
                                    |
                                    v merged through Redux
 +-------------------------------------------------------------------+
 | Charts (Table, Big Number, ECharts Timeseries, Pivot Table)       |
 |  - call applyDashboardComparison(formData)                        |
 |  - if follow_dashboard_comparison !== false:                      |
 |      the local time_compare is overridden by the dashboard one    |
 +----------------------------------+--------------------------------+
                                    |
                                    v buildQuery() -> POST /api/v1/chart/data
 +-------------------------------------------------------------------+
 | Superset backend (QueryContextProcessor / helpers.py)             |
 |  1. Runs the main query on the reference period                   |
 |  2. Runs a secondary query on the comparison period (offset)      |
 |  3. In join_offset_dfs():                                         |
 |     - computes the temporal shift (whole months or days)          |
 |     - shifts the time column of the comparison query              |
 |     - runs an outer/left join that realigns the series            |
 |  4. Runs compare.py when a difference or percentage is requested  |
 +----------------------------------+--------------------------------+
                                    |
                                    v consolidated DataFrame
 +-------------------------------------------------------------------+
 | Visualization frontend (transformProps)                           |
 |  - renders side by side metrics, overlaid series or variations    |
 +-------------------------------------------------------------------+
```

The contract between the filter, the helper and the backend is specified in [data-contract.md](data-contract.md).

## 3. Edge cases in the temporal shift

The shift computed in `helpers.py` distinguishes two modes:

- **Whole month shift (`pd.DateOffset(months=N)`).**
  Used when both start dates fall on day 1 of a month (for example 1 September against 1 August). It keeps the last day of the month aligned across months of 30 and 31 days.
- **Day shift (`pd.DateOffset(days=N)`).**
  Used for intra month periods or arbitrary ranges (for example from the 12th to the 24th). The shift is exactly the number of days between the two start dates.
- **Periods of different length.**
  Positions that have no counterpart (March has 31 days, February 28) stay empty at the end of the series. They are never shifted.
- **Leap years.**
  29 February compared with the previous year maps to 28 February without out of range errors.

## 4. Multiple date columns

For datasets with several date columns (order date, shipping date, invoice date):

- Every chart keeps its own time column by default (x axis or metric configuration).
- If a `reference_column` is set in the PeriodCompare filter configuration, it is propagated through `granularity_sqla` to target that dimension. Only a plain column name is propagated, never an ad hoc column.

## 5. Frontend integration notes

- **One shared helper.** Every chart calls `applyDashboardComparison(formData)` at the top of `buildQuery` and `transformProps`. The helper is generic on the form data type, so each chart keeps its own typed form data.
- **Opt in per chart.** A chart that does not know the `metric__<offset>` columns is not forced to follow the comparison, because the series pivot pipeline of ECharts would break on unexpected columns. The control `follow_dashboard_comparison` lets a chart opt out.
- **Stable filter state.** The filter applies its data mask once per distinct state of the controls. Re-applying the mask on every render makes the dashboard state change, which re-renders the filter in an infinite loop.
