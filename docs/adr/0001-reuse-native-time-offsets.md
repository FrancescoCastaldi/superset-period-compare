# 0001. Reuse the native time offsets of Superset

Status: Accepted (2026-10-24)

## Context

Comparing a reference period with a comparison period in Superset usually ends in Cartesian SQL views: the fact view is crossed with all months and joined back on an `OR` condition. In the case that started this project this multiplied the rows by 39 and added latencies of several seconds.

Superset 6.1.0 already contains most of what is needed: `time_offsets` accepts an explicit range (`"YYYY-MM-DD : YYYY-MM-DD"`) when `DATE_RANGE_TIMESHIFTS_ENABLED` is on, each offset runs one extra query on the comparison period, and `compare.py` computes difference, percentage and ratio. What is missing is a dashboard filter that sets the two periods, the wiring to the charts and the alignment of the time axis for range offsets.

## Decision

Build on `time_offsets` and the existing `compare` post processing. Add only the missing pieces: a native filter that emits `time_range`, `time_compare` and `comparison_type`, one shared helper (`applyDashboardComparison`) that every chart calls, and the temporal alignment of the comparison dataframe in `helpers.py`.

Do not use a second temporal filter (a query has a single `TEMPORAL_RANGE`), Jinja templating or `custom_form_data` (it is dropped by the frontend merge and by `merge_extra_form_data`).

## Consequences

- The dataset needs a single time column and no helper view; a comparison costs two light queries.
- The code added to Superset is small, but it touches upstream files, so every Superset upgrade needs a compatibility check ([upgrading](../upgrading.md)).
- Each chart opts in through the helper. A chart that does not know the `metric__<offset>` columns is not forced to follow the comparison.
