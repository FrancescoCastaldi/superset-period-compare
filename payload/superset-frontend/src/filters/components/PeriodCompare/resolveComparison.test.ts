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

import {
  resolveComparison,
  parseRange,
} from './resolveComparison';

describe('resolveComparison pure date arithmetic suite (28 cases)', () => {
  // 1. previous_month standard
  test('1. previous_month standard 30-day month', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-08-01 : 2026-09-01');
  });

  // 2. previous_month on 31-day month
  test('2. previous_month on 31-day month', () => {
    const res = resolveComparison({
      referenceRange: '2026-08-01 : 2026-09-01',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-07-01 : 2026-08-01');
  });

  // 3. previous_month on March to April (preceding Feb)
  test('3. previous_month on March to April', () => {
    const res = resolveComparison({
      referenceRange: '2026-03-01 : 2026-04-01',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-02-01 : 2026-03-01');
  });

  // 4. previous_month clamping on March 31 -> Feb 28
  test('4. previous_month clamping on March 31 -> Feb 28', () => {
    const res = resolveComparison({
      referenceRange: '2026-03-31 : 2026-04-30',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-02-28 : 2026-03-30');
  });

  // 5. previous_month clamping on March 31 in leap year 2024 -> Feb 29
  test('5. previous_month clamping on March 31 in leap year 2024 -> Feb 29', () => {
    const res = resolveComparison({
      referenceRange: '2024-03-31 : 2024-04-30',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2024-02-29 : 2024-03-30');
  });

  // 6. previous_year normal year
  test('6. previous_year normal year', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'previous_year',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2025-09-01 : 2025-10-01');
  });

  // 7. previous_year leap day 2024-02-29 -> 2023-02-28
  test('7. previous_year leap day 2024-02-29 -> 2023-02-28', () => {
    const res = resolveComparison({
      referenceRange: '2024-02-29 : 2024-03-01',
      comparisonMode: 'previous_year',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2023-02-28 : 2023-03-01');
  });

  // 8. previous_year across year end
  test('8. previous_year across year end', () => {
    const res = resolveComparison({
      referenceRange: '2026-12-01 : 2027-01-01',
      comparisonMode: 'previous_year',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2025-12-01 : 2026-01-01');
  });

  // 9. previous_period 1 full month
  test('9. previous_period 1 full month', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-08-01 : 2026-09-01');
  });

  // 10. previous_period 2 full months
  test('10. previous_period 2 full months', () => {
    const res = resolveComparison({
      referenceRange: '2026-07-01 : 2026-09-01',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-05-01 : 2026-07-01');
  });

  // 11. previous_period 7 days
  test('11. previous_period 7 days', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-08 : 2026-09-15',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-09-01 : 2026-09-08');
  });

  // 12. previous_period 1 day
  test('12. previous_period 1 day', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-02 : 2026-09-03',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-09-01 : 2026-09-02');
  });

  // 13. previous_period crossing year boundary
  test('13. previous_period crossing year boundary', () => {
    const res = resolveComparison({
      referenceRange: '2026-01-01 : 2026-02-01',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2025-12-01 : 2026-01-01');
  });

  // 14. previous_period arbitrary 10 days
  test('14. previous_period arbitrary 10 days', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-10 : 2026-09-20',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-08-31 : 2026-09-10');
  });

  // 15. custom mode valid
  test('15. custom mode valid', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'custom',
      customRange: '2026-01-01 : 2026-02-01',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-01-01 : 2026-02-01');
  });

  // 16. custom mode missing customRange
  test('16. custom mode missing customRange', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'custom',
      customRange: null,
    });
    expect(res.isActive).toBe(false);
    expect(res.comparisonRange).toBeNull();
  });

  // 17. custom mode invalid string
  test('17. custom mode invalid string', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'custom',
      customRange: 'invalid',
    });
    expect(res.isActive).toBe(false);
    expect(res.comparisonRange).toBeNull();
  });

  // 18. none mode
  test('18. none mode returns inactive', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'none',
    });
    expect(res.isActive).toBe(false);
    expect(res.comparisonRange).toBeNull();
  });

  // 19. empty referenceRange
  test('19. empty referenceRange returns inactive', () => {
    const res = resolveComparison({
      referenceRange: '',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(false);
    expect(res.comparisonRange).toBeNull();
  });

  // 20. null referenceRange
  test('20. null referenceRange returns inactive', () => {
    const res = resolveComparison({
      referenceRange: null,
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(false);
    expect(res.comparisonRange).toBeNull();
  });

  // 21. malformed referenceRange
  test('21. malformed referenceRange returns inactive', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(false);
    expect(res.comparisonRange).toBeNull();
  });

  // 22. colon without spaces
  test('22. colon without spaces parses correctly', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01:2026-10-01',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-08-01 : 2026-09-01');
  });

  // 23. colon with spaces
  test('23. colon with spaces parses correctly', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01 : 2026-10-01',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-08-01 : 2026-09-01');
  });

  // 24. ISO timestamps with T00:00:00
  test('24. ISO timestamps with T00:00:00', () => {
    const res = resolveComparison({
      referenceRange: '2026-09-01T00:00:00 : 2026-10-01T23:59:59',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-08-01 : 2026-09-01');
  });

  // 25. previous_year on January 1st
  test('25. previous_year on January 1st', () => {
    const res = resolveComparison({
      referenceRange: '2026-01-01 : 2026-02-01',
      comparisonMode: 'previous_year',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2025-01-01 : 2025-02-01');
  });

  // 26. previous_month on January shifts to December prior year
  test('26. previous_month on January shifts to December prior year', () => {
    const res = resolveComparison({
      referenceRange: '2026-01-01 : 2026-02-01',
      comparisonMode: 'previous_month',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2025-12-01 : 2026-01-01');
  });

  // 27. 3-month quarter previous_period
  test('27. 3-month quarter previous_period', () => {
    const res = resolveComparison({
      referenceRange: '2026-04-01 : 2026-07-01',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2026-01-01 : 2026-04-01');
  });

  // 28. full year previous_period
  test('28. full year previous_period', () => {
    const res = resolveComparison({
      referenceRange: '2026-01-01 : 2027-01-01',
      comparisonMode: 'previous_period',
    });
    expect(res.isActive).toBe(true);
    expect(res.comparisonRange).toBe('2025-01-01 : 2026-01-01');
  });
});
