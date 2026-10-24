import assert from 'node:assert/strict';

function pad(num) {
  return String(num).padStart(2, '0');
}

function formatDate(d) {
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
}

function parseDate(str) {
  const trimmed = str.trim();
  if (!trimmed) return null;
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

function parseRange(rangeStr) {
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

function addMonthsClamped(date, months) {
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

function addYearsClamped(date, years) {
  return addMonthsClamped(date, years * 12);
}

function resolveComparison(options) {
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

  let compStart;
  let compEnd;

  if (comparisonMode === 'previous_month') {
    compStart = addMonthsClamped(refStart, -1);
    compEnd = addMonthsClamped(refEnd, -1);
  } else if (comparisonMode === 'previous_year') {
    compStart = addYearsClamped(refStart, -1);
    compEnd = addYearsClamped(refEnd, -1);
  } else if (comparisonMode === 'previous_period') {
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

const tests = [
  // 1
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-08-01 : 2026-09-01');
  },
  // 2
  () => {
    const res = resolveComparison({ referenceRange: '2026-08-01 : 2026-09-01', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-07-01 : 2026-08-01');
  },
  // 3
  () => {
    const res = resolveComparison({ referenceRange: '2026-03-01 : 2026-04-01', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-02-01 : 2026-03-01');
  },
  // 4
  () => {
    const res = resolveComparison({ referenceRange: '2026-03-31 : 2026-04-30', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-02-28 : 2026-03-30');
  },
  // 5
  () => {
    const res = resolveComparison({ referenceRange: '2024-03-31 : 2024-04-30', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2024-02-29 : 2024-03-30');
  },
  // 6
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'previous_year' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2025-09-01 : 2025-10-01');
  },
  // 7
  () => {
    const res = resolveComparison({ referenceRange: '2024-02-29 : 2024-03-01', comparisonMode: 'previous_year' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2023-02-28 : 2023-03-01');
  },
  // 8
  () => {
    const res = resolveComparison({ referenceRange: '2026-12-01 : 2027-01-01', comparisonMode: 'previous_year' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2025-12-01 : 2026-01-01');
  },
  // 9
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-08-01 : 2026-09-01');
  },
  // 10
  () => {
    const res = resolveComparison({ referenceRange: '2026-07-01 : 2026-09-01', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-05-01 : 2026-07-01');
  },
  // 11
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-08 : 2026-09-15', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-09-01 : 2026-09-08');
  },
  // 12
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-02 : 2026-09-03', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-09-01 : 2026-09-02');
  },
  // 13
  () => {
    const res = resolveComparison({ referenceRange: '2026-01-01 : 2026-02-01', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2025-12-01 : 2026-01-01');
  },
  // 14
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-10 : 2026-09-20', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-08-31 : 2026-09-10');
  },
  // 15
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'custom', customRange: '2026-01-01 : 2026-02-01' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-01-01 : 2026-02-01');
  },
  // 16
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'custom', customRange: null });
    assert.equal(res.isActive, false);
    assert.equal(res.comparisonRange, null);
  },
  // 17
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'custom', customRange: 'invalid' });
    assert.equal(res.isActive, false);
    assert.equal(res.comparisonRange, null);
  },
  // 18
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'none' });
    assert.equal(res.isActive, false);
    assert.equal(res.comparisonRange, null);
  },
  // 19
  () => {
    const res = resolveComparison({ referenceRange: '', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, false);
    assert.equal(res.comparisonRange, null);
  },
  // 20
  () => {
    const res = resolveComparison({ referenceRange: null, comparisonMode: 'previous_month' });
    assert.equal(res.isActive, false);
    assert.equal(res.comparisonRange, null);
  },
  // 21
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, false);
    assert.equal(res.comparisonRange, null);
  },
  // 22
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01:2026-10-01', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-08-01 : 2026-09-01');
  },
  // 23
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01 : 2026-10-01', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-08-01 : 2026-09-01');
  },
  // 24
  () => {
    const res = resolveComparison({ referenceRange: '2026-09-01T00:00:00 : 2026-10-01T23:59:59', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-08-01 : 2026-09-01');
  },
  // 25
  () => {
    const res = resolveComparison({ referenceRange: '2026-01-01 : 2026-02-01', comparisonMode: 'previous_year' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2025-01-01 : 2025-02-01');
  },
  // 26
  () => {
    const res = resolveComparison({ referenceRange: '2026-01-01 : 2026-02-01', comparisonMode: 'previous_month' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2025-12-01 : 2026-01-01');
  },
  // 27
  () => {
    const res = resolveComparison({ referenceRange: '2026-04-01 : 2026-07-01', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2026-01-01 : 2026-04-01');
  },
  // 28
  () => {
    const res = resolveComparison({ referenceRange: '2026-01-01 : 2027-01-01', comparisonMode: 'previous_period' });
    assert.equal(res.isActive, true);
    assert.equal(res.comparisonRange, '2025-01-01 : 2026-01-01');
  },
];

tests.forEach((t, i) => {
  t();
  console.log(`resolveComparison test ${i + 1}/28 passed`);
});

console.log('ALL 28 resolveComparison TESTS PASSED SUCCESSFULLY!');
