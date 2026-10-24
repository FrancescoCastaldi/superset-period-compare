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

export type ComparisonPreset =
  | 'none'
  | 'previous_period'
  | 'previous_month'
  | 'previous_year'
  | 'custom';

export interface ResolveComparisonOptions {
  referenceRange?: string | null;
  comparisonMode?: ComparisonPreset;
  customRange?: string | null;
}

export interface ResolvedComparison {
  referenceRange: string;
  comparisonRange: string | null;
  isActive: boolean;
  label: string;
}

function pad(num: number): string {
  return String(num).padStart(2, '0');
}

function formatDate(d: Date): string {
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
}

function parseDate(str: string): Date | null {
  const trimmed = str.trim();
  if (!trimmed) return null;
  // Handle ISO or YYYY-MM-DD
  const parts = trimmed.split('T')[0].split('-');
  if (parts.length === 3) {
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10) - 1;
    const d = parseInt(parts[2], 10);
    if (!isNaN(y) && !isNaN(m) && !isNaN(d)) {
      return new Date(Date.UTC(y, m, d));
    }
  }
  const parsed = new Date(trimmed);
  return isNaN(parsed.getTime()) ? null : parsed;
}

export function parseRange(rangeStr?: string | null): [Date, Date] | null {
  if (!rangeStr) return null;
  const separator = rangeStr.includes(' : ') ? ' : ' : ':';
  const parts = rangeStr.split(separator);
  if (parts.length !== 2) return null;

  const start = parseDate(parts[0]);
  const end = parseDate(parts[1]);
  if (!start || !end || isNaN(start.getTime()) || isNaN(end.getTime())) {
    return null;
  }
  return [start, end];
}

function addMonthsClamped(date: Date, months: number): Date {
  const year = date.getUTCFullYear();
  const month = date.getUTCMonth();
  const day = date.getUTCDate();

  const targetMonth = month + months;
  const targetDate = new Date(Date.UTC(year, targetMonth, 1));
  const maxDays = new Date(
    Date.UTC(targetDate.getUTCFullYear(), targetDate.getUTCMonth() + 1, 0),
  ).getUTCDate();

  const clampedDay = Math.min(day, maxDays);
  return new Date(
    Date.UTC(targetDate.getUTCFullYear(), targetDate.getUTCMonth(), clampedDay),
  );
}

function addYearsClamped(date: Date, years: number): Date {
  return addMonthsClamped(date, years * 12);
}

export function resolveComparison(
  options: ResolveComparisonOptions,
): ResolvedComparison {
  const {
    referenceRange,
    comparisonMode = 'none',
    customRange = null,
  } = options;

  if (!referenceRange || comparisonMode === 'none') {
    return {
      referenceRange: referenceRange || '',
      comparisonRange: null,
      isActive: false,
      label: referenceRange || 'No filter',
    };
  }

  if (comparisonMode === 'custom') {
    if (!customRange) {
      return {
        referenceRange,
        comparisonRange: null,
        isActive: false,
        label: referenceRange,
      };
    }
    const parsedCustom = parseRange(customRange);
    if (!parsedCustom) {
      return {
        referenceRange,
        comparisonRange: null,
        isActive: false,
        label: referenceRange,
      };
    }
    const compStr = `${formatDate(parsedCustom[0])} : ${formatDate(parsedCustom[1])}`;
    return {
      referenceRange,
      comparisonRange: compStr,
      isActive: true,
      label: `${referenceRange} vs ${compStr}`,
    };
  }

  const parsed = parseRange(referenceRange);
  if (!parsed) {
    return {
      referenceRange,
      comparisonRange: null,
      isActive: false,
      label: referenceRange,
    };
  }

  const [refStart, refEnd] = parsed;

  let compStart: Date;
  let compEnd: Date;

  if (comparisonMode === 'previous_month') {
    compStart = addMonthsClamped(refStart, -1);
    compEnd = addMonthsClamped(refEnd, -1);
  } else if (comparisonMode === 'previous_year') {
    compStart = addYearsClamped(refStart, -1);
    compEnd = addYearsClamped(refEnd, -1);
  } else if (comparisonMode === 'previous_period') {
    // If range is exact full month(s) from 1st to 1st
    const isFirstToFirst =
      refStart.getUTCDate() === 1 && refEnd.getUTCDate() === 1;
    if (isFirstToFirst) {
      const monthDiff =
        (refEnd.getUTCFullYear() - refStart.getUTCFullYear()) * 12 +
        (refEnd.getUTCMonth() - refStart.getUTCMonth());
      compStart = addMonthsClamped(refStart, -monthDiff);
      compEnd = refStart;
    } else {
      const diffMs = refEnd.getTime() - refStart.getTime();
      compEnd = new Date(refStart.getTime());
      compStart = new Date(refStart.getTime() - diffMs);
    }
  } else {
    return {
      referenceRange,
      comparisonRange: null,
      isActive: false,
      label: referenceRange,
    };
  }

  const compStr = `${formatDate(compStart)} : ${formatDate(compEnd)}`;
  return {
    referenceRange,
    comparisonRange: compStr,
    isActive: true,
    label: `${referenceRange} vs ${compStr}`,
  };
}
