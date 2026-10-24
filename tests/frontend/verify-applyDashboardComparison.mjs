import assert from 'node:assert/strict';

// Inline definition of ComparisonType matching @superset-ui/core
const ComparisonType = {
  Values: 'values',
  Difference: 'difference',
  Percentage: 'percentage',
  Ratio: 'ratio',
};

function ensureIsArray(val) {
  if (val === undefined || val === null) return [];
  return Array.isArray(val) ? val : [val];
}

const SUPPORTED_COMPARISON_VIZ_TYPES = new Set([
  'table',
  'pivot_table_v2',
  'pop_kpi',
  'big_number',
  'big_number_total',
  'echarts_area',
  'mixed_timeseries',
]);

function isComparisonSupported(vizType) {
  if (!vizType) {
    return true;
  }
  return (
    SUPPORTED_COMPARISON_VIZ_TYPES.has(vizType) ||
    vizType.startsWith('echarts_timeseries')
  );
}

function applyDashboardComparison(formData) {
  if (!formData) {
    return {
      formData,
      timeOffsets: [],
      comparisonType: ComparisonType.Values,
      isComparing: false,
    };
  }

  // Graceful degradation for chart types that do not support time comparison
  if (formData.viz_type && !isComparisonSupported(formData.viz_type)) {
    return {
      formData,
      timeOffsets: [],
      comparisonType:
        formData.comparison_type || ComparisonType.Values,
      isComparing: false,
    };
  }

  const followDashboard = formData?.follow_dashboard_comparison !== false;
  const extraFormData = formData?.extra_form_data || {};

  const dashboardCompare = extraFormData.time_compare;
  const dashboardType = extraFormData.comparison_type;

  let timeOffsets = [];
  let comparisonType = ComparisonType.Values;
  let isComparing = false;

  if (followDashboard && dashboardCompare) {
    const rawOffsets = ensureIsArray(dashboardCompare);
    timeOffsets = rawOffsets.filter(Boolean);
    if (timeOffsets.length > 0) {
      isComparing = true;
      comparisonType =
        dashboardType ||
        formData.comparison_type ||
        ComparisonType.Values;
    }
  }

  if (!isComparing) {
    if (formData?.time_compare) {
      const rawOffsets = ensureIsArray(formData.time_compare);
      timeOffsets = rawOffsets.filter(Boolean);
      if (timeOffsets.length > 0) {
        isComparing = true;
        comparisonType =
          formData.comparison_type || ComparisonType.Values;
      }
    }
  }

  const updatedFormData = {
    ...formData,
    ...(isComparing
      ? {
          time_compare: timeOffsets,
          comparison_type: comparisonType,
        }
      : {}),
  };

  return {
    formData: updatedFormData,
    timeOffsets,
    comparisonType,
    isComparing,
  };
}

function resolveTimeOffsets(formData) {
  return applyDashboardComparison(formData).timeOffsets;
}

// 1. Dashboard comparison overrides chart local comparison when active
{
  const formData = {
    viz_type: 'table',
    time_compare: ['1 year ago'],
    comparison_type: ComparisonType.Difference,
    extra_form_data: {
      time_compare: '2026-08-01 : 2026-09-01',
      comparison_type: 'values',
    },
  };
  const result = applyDashboardComparison(formData);
  assert.equal(result.isComparing, true);
  assert.deepEqual(result.timeOffsets, ['2026-08-01 : 2026-09-01']);
  assert.equal(result.comparisonType, ComparisonType.Values);
  assert.deepEqual(result.formData.time_compare, ['2026-08-01 : 2026-09-01']);
  assert.equal(result.formData.comparison_type, ComparisonType.Values);
  console.log('Test 1 passed: dashboard comparison overrides chart local');
}

// 2. No comparison when time_compare is empty or absent
{
  const formData = {
    viz_type: 'table',
    extra_form_data: {},
  };
  const result = applyDashboardComparison(formData);
  assert.equal(result.isComparing, false);
  assert.deepEqual(result.timeOffsets, []);
  assert.equal(result.comparisonType, ComparisonType.Values);
  console.log('Test 2 passed: no comparison when empty');
}

// 3. follow_dashboard_comparison false keeps chart local comparison
{
  const formData = {
    viz_type: 'table',
    follow_dashboard_comparison: false,
    time_compare: ['1 year ago'],
    comparison_type: ComparisonType.Ratio,
    extra_form_data: {
      time_compare: '2026-08-01 : 2026-09-01',
      comparison_type: 'values',
    },
  };
  const result = applyDashboardComparison(formData);
  assert.equal(result.isComparing, true);
  assert.deepEqual(result.timeOffsets, ['1 year ago']);
  assert.equal(result.comparisonType, ComparisonType.Ratio);
  console.log('Test 3 passed: follow_dashboard_comparison false keeps local');
}

// 4. resolveTimeOffsets
{
  const formData = {
    extra_form_data: {
      time_compare: '2026-08-01 : 2026-09-01',
    },
  };
  const offsets = resolveTimeOffsets(formData);
  assert.deepEqual(offsets, ['2026-08-01 : 2026-09-01']);
  console.log('Test 4 passed: resolveTimeOffsets with interval');
}

// 5. resolveTimeOffsets inactive
{
  const formData = {};
  const offsets = resolveTimeOffsets(formData);
  assert.deepEqual(offsets, []);
  console.log('Test 5 passed: resolveTimeOffsets inactive');
}

// 6. Graceful degradation for unsupported chart types (e.g. sankey, treemap)
{
  const formData = {
    viz_type: 'sankey',
    extra_form_data: {
      time_compare: '2026-08-01 : 2026-09-01',
      comparison_type: 'values',
    },
  };
  const result = applyDashboardComparison(formData);
  assert.equal(result.isComparing, false);
  assert.deepEqual(result.timeOffsets, []);
  assert.equal(result.comparisonType, ComparisonType.Values);
  assert.deepEqual(result.formData, formData);
  assert.equal(result.formData.time_compare, undefined);
  console.log('Test 6 passed: graceful degradation for unsupported chart type (sankey)');
}

// 7. resolveTimeOffsets on unsupported chart returns empty array
{
  const formData = {
    viz_type: 'treemap',
    extra_form_data: {
      time_compare: '2026-08-01 : 2026-09-01',
    },
  };
  const offsets = resolveTimeOffsets(formData);
  assert.deepEqual(offsets, []);
  console.log('Test 7 passed: resolveTimeOffsets returns empty array for unsupported chart type (treemap)');
}

// 8. isComparisonSupported correctly classifies viz types
{
  assert.equal(isComparisonSupported('sankey'), false);
  assert.equal(isComparisonSupported('treemap'), false);
  assert.equal(isComparisonSupported('pie'), false);
  assert.equal(isComparisonSupported('table'), true);
  assert.equal(isComparisonSupported('pivot_table_v2'), true);
  assert.equal(isComparisonSupported('pop_kpi'), true);
  assert.equal(isComparisonSupported('echarts_timeseries_line'), true);
  assert.equal(isComparisonSupported('echarts_timeseries_bar'), true);
  assert.equal(isComparisonSupported(undefined), true);
  console.log('Test 8 passed: isComparisonSupported classification');
}

console.log('ALL CONTRACT TESTS PASSED (8/8)');
