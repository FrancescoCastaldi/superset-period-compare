/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { ComparisonType } from '@superset-ui/core';
import {
  applyDashboardComparison,
  resolveTimeOffsets,
} from '../../src/utils/applyDashboardComparison';

describe('applyDashboardComparison contract tests', () => {
  test('dashboard comparison overrides chart local comparison when active', () => {
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
    expect(result.isComparing).toBe(true);
    expect(result.timeOffsets).toEqual(['2026-08-01 : 2026-09-01']);
    expect(result.comparisonType).toBe(ComparisonType.Values);
    expect(result.formData.time_compare).toEqual(['2026-08-01 : 2026-09-01']);
    expect(result.formData.comparison_type).toBe(ComparisonType.Values);
  });

  test('no comparison when time_compare is empty or absent', () => {
    const formData = {
      viz_type: 'table',
      extra_form_data: {},
    };

    const result = applyDashboardComparison(formData);
    expect(result.isComparing).toBe(false);
    expect(result.timeOffsets).toEqual([]);
    expect(result.comparisonType).toBe(ComparisonType.Values);
  });

  test('follow_dashboard_comparison false keeps chart local comparison', () => {
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
    expect(result.isComparing).toBe(true);
    expect(result.timeOffsets).toEqual(['1 year ago']);
    expect(result.comparisonType).toBe(ComparisonType.Ratio);
  });
});

describe('resolveTimeOffsets contract tests', () => {
  test('returns normalized array from dashboard extra_form_data interval', () => {
    const formData = {
      extra_form_data: {
        time_compare: '2026-08-01 : 2026-09-01',
      },
    };

    const offsets = resolveTimeOffsets(formData);
    expect(offsets).toEqual(['2026-08-01 : 2026-09-01']);
  });

  test('returns empty array when comparison is inactive', () => {
    const formData = {};
    const offsets = resolveTimeOffsets(formData);
    expect(offsets).toEqual([]);
  });
});
