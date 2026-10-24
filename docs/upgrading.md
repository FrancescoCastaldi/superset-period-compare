# Upgrading to New Superset Versions

This guide explains how to keep or move the Period Compare patch when a new minor or major version of Apache Superset is released (for example 6.2.0 or 7.0.0).

## 1. Compatibility check

Before applying the patch to a new Superset release:

1. Run a verification:
   ```cmd
   bin\verify.bat D:\Path\To\New\Superset
   ```
2. The installer compares every file with the hashes in `compat/compat.json`. If some upstream files changed in the meantime (for example new lines in `helpers.py`), they are reported as `ModifiedOrCustom` instead of matching upstream.

## 2. Files touched by the patch

The patch touches three well defined areas.

### Python backend
- `superset/models/helpers.py`: alignment and join logic in `join_offset_dfs` and `processing_time_offsets`.
- `superset/common/query_object.py`: support for time strings in `_is_valid_date_range`.
- `superset/constants.py`: mapping of `time_compare` and `comparison_type` in `EXTRA_FORM_DATA_OVERRIDE_REGULAR_MAPPINGS`.
- `superset/config.py`: enables the feature flag `DATE_RANGE_TIMESHIFTS_ENABLED: True`.

### Frontend core and controls
- `packages/superset-ui-chart-controls/src/utils/applyDashboardComparison.ts`: normalization helper.
- `packages/superset-ui-chart-controls/src/sections/timeComparison.tsx`: the `follow_dashboard_comparison` control.
- `packages/superset-ui-core/src/query/constants.ts`: override mapping constant.

### Native filter and registrations
- `src/filters/components/PeriodCompare/`: self contained, independent module.
- `src/visualizations/presets/MainPreset.ts`: the markers `period-compare:begin` and `period-compare:end`.

## 3. Regenerating the payload for the new release

Once the new Superset version is aligned in your development environment:

1. Port the changes to the working branch of the new version and commit them.
2. Run the extraction script:
   ```powershell
   powershell -File scripts/make-payload.ps1 -WorktreePath "D:\Path\To\NewSuperset" -BaseTag "6.2.0"
   ```
3. The script copies the new files into `payload/` and rewrites `compat/compat.json` with the exact hashes of the new baseline.
4. Run the Pester suite to validate installation and rollback:
   ```powershell
   Invoke-Pester tests/installer
   ```
5. Compile the patched tree with the real Superset toolchain and fix every TypeScript error. The Node and Python test suites of this repository do not run the TypeScript compiler, so a green test run does not prove that the frontend builds.
