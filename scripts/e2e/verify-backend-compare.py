#!/usr/bin/env python3
"""
Verifies the period comparison of the patched Superset backend.

For every case it queries /api/v1/chart/data with a reference period and a comparison
period (time_offsets in range format) and compares each returned value with a direct
SQL query on the test database (load-fixtures-postgres.py).

Usage (inside the Superset container, after setup-test-dashboard.py):
    python verify-backend-compare.py --base http://localhost:8088

Exits with code 1 if at least one check fails.
"""

import argparse
import importlib.util
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

import psycopg2

TOLERANCE = Decimal("0.01")


def load_setup_module():
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("setup_test_dashboard", os.path.join(here, "setup-test-dashboard.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_months(day, months):
    month_index = day.year * 12 + day.month - 1 + months
    year, month = divmod(month_index, 12)
    month += 1
    # same logic as pd.DateOffset(months=n): the day is clamped to the end of the month
    last = (date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)).day
    return date(year, month, min(day.day, last))


class Verifier:
    def __init__(self, api, dataset_id, pg):
        self.api = api
        self.dataset_id = dataset_id
        self.pg = pg
        self.failures = 0
        self.checks = 0

    # --- reference SQL ------------------------------------------------------
    def sql_total(self, start, end, group=None):
        with self.pg.cursor() as cur:
            if group:
                cur.execute(
                    f"SELECT {group}, SUM(sales_amount) FROM sales_performance "
                    "WHERE order_date >= %s AND order_date < %s GROUP BY 1",
                    (start, end),
                )
                return {row[0]: row[1] for row in cur.fetchall()}
            cur.execute(
                "SELECT COALESCE(SUM(sales_amount), 0) FROM sales_performance WHERE order_date >= %s AND order_date < %s",
                (start, end),
            )
            return cur.fetchone()[0]

    def sql_daily(self, start, end):
        with self.pg.cursor() as cur:
            cur.execute(
                "SELECT order_date, SUM(sales_amount) FROM sales_performance "
                "WHERE order_date >= %s AND order_date < %s GROUP BY 1",
                (start, end),
            )
            return {row[0]: row[1] for row in cur.fetchall()}

    def sql_monthly(self, start, end):
        with self.pg.cursor() as cur:
            cur.execute(
                "SELECT date_trunc('month', order_date)::date, SUM(sales_amount) FROM sales_performance "
                "WHERE order_date >= %s AND order_date < %s GROUP BY 1",
                (start, end),
            )
            return {row[0]: row[1] for row in cur.fetchall()}

    # --- API call -----------------------------------------------------------
    def query(self, ref, comp, columns=None, post_processing=None):
        body = {
            "datasource": {"id": self.dataset_id, "type": "table"},
            "force": True,
            "queries": [
                {
                    "filters": [{"col": "order_date", "op": "TEMPORAL_RANGE", "val": ref}],
                    "columns": columns or [],
                    "metrics": ["sum_sales"],
                    "time_offsets": [comp],
                    "post_processing": post_processing or [],
                    "row_limit": 10000,
                    "orderby": [],
                    "extras": {},
                }
            ],
            "result_format": "json",
            "result_type": "full",
        }
        result = self.api.call("POST", "/api/v1/chart/data", body)["result"][0]
        if result.get("error"):
            sys.exit(f"backend error: {result['error']}")
        return result["data"]

    # --- checks -------------------------------------------------------------
    def check(self, case, label, got, expected):
        self.checks += 1
        got_d = None if got is None else Decimal(str(got))
        exp_d = None if expected is None else Decimal(str(expected))
        if exp_d is None or exp_d == 0 and got_d is None:
            ok = got_d is None or got_d == 0
        else:
            ok = got_d is not None and abs(got_d - exp_d) <= TOLERANCE
        status = "PASS" if ok else "FAIL"
        if not ok:
            self.failures += 1
        print(f"  [{status}] {case} {label}: expected={exp_d} got={got_d}")

    def case_totals(self, case, ref, comp):
        rs, re_ = [d.strip() for d in ref.split(" : ")]
        cs, ce = [d.strip() for d in comp.split(" : ")]
        rows = self.query(ref, comp)
        assert len(rows) == 1, rows
        row = rows[0]
        comp_key = f"sum_sales__{comp}"
        self.check(case, "reference", row.get("sum_sales"), self.sql_total(rs, re_))
        self.check(case, "comparison", row.get(comp_key), self.sql_total(cs, ce))

    def case_group(self, case, ref, comp, column):
        rs, re_ = [d.strip() for d in ref.split(" : ")]
        cs, ce = [d.strip() for d in comp.split(" : ")]
        rows = {r[column]: r for r in self.query(ref, comp, columns=[column])}
        ref_sql = self.sql_total(rs, re_, column)
        comp_sql = self.sql_total(cs, ce, column)
        for key in sorted(ref_sql):
            self.check(case, f"{key} reference", rows[key].get("sum_sales"), ref_sql[key])
            self.check(case, f"{key} comparison", rows[key].get(f"sum_sales__{comp}"), comp_sql.get(key))

    def case_compare_types(self, case, ref, comp):
        rs, re_ = [d.strip() for d in ref.split(" : ")]
        cs, ce = [d.strip() for d in comp.split(" : ")]
        ref_v, comp_v = self.sql_total(rs, re_), self.sql_total(cs, ce)
        expected = {
            "difference": ref_v - comp_v,
            "percentage": (ref_v - comp_v) / comp_v,
            "ratio": ref_v / comp_v,
        }
        for compare_type, exp in expected.items():
            rule = {
                "operation": "compare",
                "options": {
                    "source_columns": ["sum_sales"],
                    "compare_columns": [f"sum_sales__{comp}"],
                    "compare_type": compare_type,
                    "drop_original_columns": False,
                },
            }
            row = self.query(ref, comp, post_processing=[rule])[0]
            key = next((k for k in row if k.startswith(f"{compare_type}__")), None)
            got = row.get(key) if key else None
            tol_ok = got is not None and abs(Decimal(str(got)) - Decimal(str(exp))) <= Decimal("0.0001")
            self.checks += 1
            if not tol_ok:
                self.failures += 1
            print(f"  [{'PASS' if tol_ok else 'FAIL'}] {case} {compare_type}: expected={exp:.6f} got={got}")

    def case_daily_alignment(self, case, ref, comp, months_shift=None, days_shift=None):
        """Daily series: day d of the reference period must carry the value of day d - shift of the comparison period."""
        rs, re_ = [d.strip() for d in ref.split(" : ")]
        cs, ce = [d.strip() for d in comp.split(" : ")]
        rows = self.query(ref, comp, columns=[{
            "timeGrain": "P1D", "columnType": "BASE_AXIS", "sqlExpression": "order_date",
            "label": "order_date", "expressionType": "SQL"}])
        ref_sql = self.sql_daily(rs, re_)
        comp_sql = self.sql_daily(cs, ce)
        by_day = {datetime.utcfromtimestamp(r["order_date"] / 1000).date(): r for r in rows}
        comp_key = f"sum_sales__{comp}"
        day = date.fromisoformat(rs)
        end = date.fromisoformat(re_)
        # Every comparison day is shifted forward by the offset. A reference day without a
        # matching day (March has 31 days, February 28) stays empty.
        comp_day = date.fromisoformat(cs)
        shifted_to_source = {}
        while comp_day < date.fromisoformat(ce):
            target = add_months(comp_day, months_shift) if months_shift else comp_day + timedelta(days=days_shift)
            shifted_to_source[target] = comp_day
            comp_day += timedelta(days=1)
        mismatches, compared = 0, 0
        while day < end:
            row = by_day.get(day)
            src_day = shifted_to_source.get(day)
            exp_ref = ref_sql.get(day)
            exp_comp = comp_sql.get(src_day) if src_day else None
            got_ref = None if row is None else row.get("sum_sales")
            got_comp = None if row is None else row.get(comp_key)
            for what, got, exp in (("reference", got_ref, exp_ref), ("comparison", got_comp, exp_comp)):
                compared += 1
                g = None if got is None else Decimal(str(got))
                e = None if exp is None else Decimal(str(exp))
                same = (g is None and e is None) or (g == 0 and e is None) or (e == 0 and g is None) or (
                    g is not None and e is not None and abs(g - e) <= TOLERANCE)
                if not same:
                    mismatches += 1
                    if mismatches <= 5:
                        print(f"    day {day} {what}: expected={e} got={g}")
            day += timedelta(days=1)
        self.checks += 1
        if mismatches:
            self.failures += 1
        print(f"  [{'PASS' if not mismatches else 'FAIL'}] {case}: {compared} daily values compared, {mismatches} differences")

    def case_monthly(self, case, ref, comp, months_shift):
        rs, re_ = [d.strip() for d in ref.split(" : ")]
        cs, ce = [d.strip() for d in comp.split(" : ")]
        rows = self.query(ref, comp, columns=[{
            "timeGrain": "P1M", "columnType": "BASE_AXIS", "sqlExpression": "order_date",
            "label": "order_date", "expressionType": "SQL"}])
        ref_sql = self.sql_monthly(rs, re_)
        comp_sql = self.sql_monthly(cs, ce)
        comp_key = f"sum_sales__{comp}"
        for r in rows:
            month = datetime.utcfromtimestamp(r["order_date"] / 1000).date().replace(day=1)
            self.check(case, f"{month:%Y-%m} reference", r.get("sum_sales"), ref_sql.get(month))
            self.check(case, f"{month:%Y-%m} comparison", r.get(comp_key), comp_sql.get(add_months(month, -months_shift)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8088")
    parser.add_argument("--user", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--pg-host", default="db-light")
    args = parser.parse_args()

    setup = load_setup_module()
    api = setup.Api(args.base, args.user, args.password)
    dataset_id = setup.find_one(api, "dataset", "table_name", "sales_performance")
    pg = psycopg2.connect(host=args.pg_host, user="superset", password="superset", dbname="pcdata")
    v = Verifier(api, dataset_id, pg)

    print("C1 previous month (totals)")
    v.case_totals("C1", "2026-09-01 : 2026-10-01", "2026-08-01 : 2026-09-01")
    print("C2 same month of the previous year (totals)")
    v.case_totals("C2", "2026-09-01 : 2026-10-01", "2025-09-01 : 2025-10-01")
    print("C3 quarter by category")
    v.case_group("C3", "2026-07-01 : 2026-10-01", "2026-04-01 : 2026-07-01", "category")
    print("C4 free ranges of 12 days")
    v.case_totals("C4", "2026-03-05 : 2026-03-17", "2026-02-10 : 2026-02-22")
    print("C5 comparison types (difference, percentage, ratio)")
    v.case_compare_types("C5", "2026-09-01 : 2026-10-01", "2026-08-01 : 2026-09-01")
    print("C6 daily series March vs February (31 days against 28, aligned by months)")
    v.case_daily_alignment("C6", "2026-03-01 : 2026-04-01", "2026-02-01 : 2026-03-01", 1)
    print("C7 daily series with free ranges (aligned by days)")
    v.case_daily_alignment("C7", "2026-03-10 : 2026-03-20", "2026-02-20 : 2026-03-02", days_shift=18)
    print("C8 monthly series quarter vs previous quarter")
    v.case_monthly("C8", "2026-07-01 : 2026-10-01", "2026-04-01 : 2026-07-01", 3)

    print(f"\nChecks: {v.checks}, failed: {v.failures}")
    sys.exit(1 if v.failures else 0)


if __name__ == "__main__":
    main()
