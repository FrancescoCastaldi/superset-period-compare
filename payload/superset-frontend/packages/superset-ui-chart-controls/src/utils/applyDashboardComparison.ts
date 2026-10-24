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

import { ComparisonType, ensureIsArray } from '@superset-ui/core';

export interface DashboardComparisonResult {
  formData: Record<string, any>;
  timeOffsets: string[];
  comparisonType: ComparisonType;
  isComparing: boolean;
}

/**
 * Applies dashboard comparison overrides to chart formData and resolves effective comparison properties.
 */
export function applyDashboardComparison(
  formData: Record<string, any>,
): DashboardComparisonResult {
  const followDashboard = formData?.follow_dashboard_comparison !== false;
  const extraFormData = formData?.extra_form_data || {};

  const dashboardCompare = extraFormData.time_compare;
  const dashboardType = extraFormData.comparison_type;

  let timeOffsets: string[] = [];
  let comparisonType: ComparisonType = ComparisonType.Values;
  let isComparing = false;

  if (followDashboard && dashboardCompare) {
    const rawOffsets = ensureIsArray(dashboardCompare);
    timeOffsets = rawOffsets.filter(Boolean);
    if (timeOffsets.length > 0) {
      isComparing = true;
      comparisonType =
        (dashboardType as ComparisonType) ||
        (formData.comparison_type as ComparisonType) ||
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
          (formData.comparison_type as ComparisonType) || ComparisonType.Values;
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

/**
 * Resolves effective time offsets for a chart from its formData and optional base query object.
 */
export function resolveTimeOffsets(
  formData: Record<string, any>,
  _baseQueryObject?: Record<string, any>,
): string[] {
  return applyDashboardComparison(formData).timeOffsets;
}
