# Data Contract: Superset Period Compare

Version: 1.1.0
Status: Frozen
Date: 2026-10-24

This document defines the formal data contract between the native dashboard filter (PeriodCompare), the intermediate form data transformation layer (`applyDashboardComparison`), the Superset analytic backend (`processing_time_offsets`, `helpers.py`, `query_object.py`) and the visualization components (Table, Big Number, ECharts Timeseries, Pivot Table).

## 1. extraFormData emitted by the PeriodCompare filter

The native PeriodCompare filter produces a dataMask object whose `extraFormData` has these keys:

```json
{
  "extraFormData": {
    "time_range": "2026-09-01 : 2026-10-01",
    "time_compare": ["2026-08-01 : 2026-09-01"],
    "comparison_type": "values"
  },
  "filterState": {
    "value": {
      "referenceRange": "2026-09-01 : 2026-10-01",
      "comparisonMode": "previous_month",
      "customRange": null,
      "comparisonType": "values"
    },
    "label": "September 2026 vs August 2026"
  }
}
```

### 1.1 Field specification

- `time_range` (string): the reference period, written as `YYYY-MM-DD : YYYY-MM-DD` or with a time part `YYYY-MM-DDTHH:MM:SS : YYYY-MM-DDTHH:MM:SS`. Ranges are half open `[start, end)`: the upper bound is excluded.
- `time_compare` (array of strings): the comparison period or periods, in the same range format. It is always an array. In the Superset types `time_compare` is declared both as `string` (`ExtraFormDataOverrideExtras`) and as `string[]` (`ExtraFormDataOverrideRegular`), so no value satisfies both and the filter emits it through an explicit cast.
- `comparison_type` (string): how the comparison is calculated. Allowed values:
  - `"values"`: raw reference and comparison values side by side.
  - `"difference"`: algebraic difference (reference - comparison).
  - `"percentage"`: percentage change ((reference - comparison) / comparison).
  - `"ratio"`: ratio (reference / comparison).
- `granularity_sqla` (string, optional): emitted only when the user sets the `reference_column` field in the filter panel, to target a specific date column when the dataset has several. A column that is not a plain name (an ad hoc column) is never emitted. When it is not set, every chart applies the filter on its own primary time column (x axis, `granularity_sqla` or native time filter).

`filterState.value` holds the state of the controls: `referenceRange`, `comparisonMode` (`none`, `previous_period`, `previous_month`, `previous_year`, `custom`), `customRange` and `comparisonType`.

## 2. Integration helpers: applyDashboardComparison and resolveTimeOffsets

Two utility functions exported by `@superset-ui/chart-controls` coordinate how the dashboard comparison is applied to each chart.

### 2.1 TypeScript signature

```typescript
export type ComparisonType = 'values' | 'difference' | 'percentage' | 'ratio';

export interface DashboardComparisonResult<
  T extends Record<string, any> = Record<string, any>,
> {
  formData: T;
  timeOffsets: string[];
  comparisonType: ComparisonType;
  isComparing: boolean;
}

export function applyDashboardComparison<T extends Record<string, any>>(
  formData: T,
): DashboardComparisonResult<T>;

export function resolveTimeOffsets(
  formData: Record<string, any>,
  baseQueryObject?: Record<string, any>,
): string[];
```

The function is generic so every chart keeps its own form data type (`SqlaFormData`, `TableChartFormData`, and so on).

### 2.2 Precedence rules

1. If the chart has `follow_dashboard_comparison === false`, the dashboard filter is ignored and the chart follows only its own comparison controls.
2. If `follow_dashboard_comparison` is true (the default), the value of `extra_form_data.time_compare` overrides any local `time_compare` of the chart.
3. If `time_compare` is missing or empty, `isComparing` is false and `timeOffsets` is an empty array.
4. The dashboard `comparison_type` takes priority over the chart `comparison_type` when it is present in `extra_form_data`. Otherwise the chart falls back to its own value or to the default `"values"`.

## 3. Backend contract: queries and column naming

### 3.1 POST /api/v1/chart/data request payload

Example of a query sent to the backend:

```json
{
  "datasource": {
    "id": 1,
    "type": "table"
  },
  "queries": [
    {
      "columns": ["order_date", "category"],
      "metrics": ["sum__sales_amount"],
      "time_range": "2026-09-01 : 2026-10-01",
      "time_offsets": ["2026-08-01 : 2026-09-01"],
      "granularity": "order_date",
      "time_grain_sqla": "P1D",
      "post_processing": [
        {
          "operation": "compare",
          "options": {
            "source_columns": ["sum__sales_amount"],
            "compare_columns": ["sum__sales_amount__2026-08-01 : 2026-09-01"],
            "compare_type": "difference"
          }
        }
      ]
    }
  ]
}
```

### 3.2 Naming of the result columns

- Reference metric: `<metric_name>` (for example `sales_amount` or `count`).
- Comparison metric for a range: `<metric_name>__<offset>` (for example `sales_amount__2026-08-01 : 2026-09-01`).
- Difference: `difference__<metric_name>__<metric_name>__<offset>`.
- Percentage change: `percentage__<metric_name>__<metric_name>__<offset>`.
- Ratio: `ratio__<metric_name>__<metric_name>__<offset>`.

### 3.3 Temporal alignment rule (backend)

When the query includes a real time column (the x axis):

1. The shift between the two ranges is computed as `delta = reference_start - comparison_start`.
2. If both starts fall on the first day of a month, the comparison dataframe is shifted by whole months (`pandas.DateOffset(months=N)`). This keeps day by day or month by month alignment perfect, without drift caused by months of 28, 30 or 31 days.
3. In every other case the shift is computed in exact days (`pandas.Timedelta(days=N)`).
4. The dataframes are joined on the shifted time column, aggregated by the time grain. For periods with a different number of days (for example 31 days against 28), the missing trailing dates have a null value (NaN or None) and no spurious shift happens.
