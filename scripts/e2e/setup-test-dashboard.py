#!/usr/bin/env python3
"""
Crea in Superset (via API REST) il database di prova, i dataset, 5 grafici e una
dashboard con il filtro nativo PeriodCompare, usando i dati di load-fixtures-postgres.py.

Uso (dentro il container di Superset):
    python setup-test-dashboard.py --base http://localhost:8088 --user admin --password admin

Lo script e' idempotente: database e dataset vengono riusati, grafici e dashboard con
lo stesso nome vengono ricreati. Stampa un JSON con gli id creati.
"""

import argparse
import http.cookiejar
import json
import sys
import urllib.error
import urllib.request

DB_NAME = "pcdata"
DB_URI_TEMPLATE = "postgresql+psycopg2://superset:superset@{host}:5432/pcdata"
DASHBOARD_SLUG = "period-compare-test"
DASHBOARD_TITLE = "Period Compare Test"
CHART_PREFIX = "PC Test"


class Api:
    def __init__(self, base, user, password):
        self.base = base.rstrip("/")
        self.token = None
        self.csrf = None
        # il token CSRF e legato alla sessione: servono i cookie
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.token = self.call(
            "POST",
            "/api/v1/security/login",
            {"username": user, "password": password, "provider": "db", "refresh": True},
        )["access_token"]
        self.csrf = self.call("GET", "/api/v1/security/csrf_token/")["result"]

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json", "Referer": self.base}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.csrf:
            headers["X-CSRFToken"] = self.csrf
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(req, timeout=120) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            sys.exit(f"{method} {path} -> {exc.code}: {exc.read().decode()[:600]}")


def find_one(api, resource, column, value):
    q = json.dumps({"filters": [{"col": column, "opr": "eq", "value": value}]})
    result = api.call("GET", f"/api/v1/{resource}/?q={urllib.request.quote(q)}")["result"]
    return result[0]["id"] if result else None


def ensure_database(api, db_host):
    db_id = find_one(api, "database", "database_name", DB_NAME)
    if db_id:
        return db_id
    return api.call(
        "POST",
        "/api/v1/database/",
        {
            "database_name": DB_NAME,
            "sqlalchemy_uri": DB_URI_TEMPLATE.format(host=db_host),
            "expose_in_sqllab": True,
        },
    )["id"]


TEMPORAL = {"order_date", "order_ts", "created_at", "closed_at"}


def ensure_dataset(api, db_id, table, main_dttm, metrics):
    ds_id = find_one(api, "dataset", "table_name", table)
    if not ds_id:
        ds_id = api.call(
            "POST", "/api/v1/dataset/", {"database": db_id, "schema": "public", "table_name": table}
        )["id"]
    detail = api.call("GET", f"/api/v1/dataset/{ds_id}")["result"]
    columns = []
    for col in detail["columns"]:
        columns.append(
            {
                "id": col["id"],
                "column_name": col["column_name"],
                "type": col["type"],
                "filterable": True,
                "groupby": True,
                "is_active": True,
                "is_dttm": col["column_name"] in TEMPORAL,
            }
        )
    # i metrici gia presenti (per esempio "count") vanno ripassati con il loro id
    existing_ids = {m["metric_name"]: m["id"] for m in detail["metrics"]}
    wanted = [{**m, **({"id": existing_ids[m["metric_name"]]} if m["metric_name"] in existing_ids else {})} for m in metrics]
    api.call(
        "PUT",
        f"/api/v1/dataset/{ds_id}",
        {"main_dttm_col": main_dttm, "columns": columns, "metrics": wanted},
    )
    return ds_id


def time_filter(column):
    return {
        "expressionType": "SIMPLE",
        "subject": column,
        "operator": "TEMPORAL_RANGE",
        "comparator": "No filter",
        "clause": "WHERE",
    }


def ensure_chart(api, ds_id, name, viz_type, form):
    existing = find_one(api, "chart", "slice_name", name)
    if existing:
        api.call("DELETE", f"/api/v1/chart/{existing}")
    params = {"datasource": f"{ds_id}__table", "viz_type": viz_type, **form}
    return api.call(
        "POST",
        "/api/v1/chart/",
        {
            "slice_name": name,
            "viz_type": viz_type,
            "datasource_id": ds_id,
            "datasource_type": "table",
            "params": json.dumps(params),
        },
    )["id"]


def build_position(chart_ids):
    """Due grafici per riga, su una griglia a 12 colonne."""
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": DASHBOARD_TITLE}},
    }
    items = list(chart_ids.items())
    for row_index in range(0, len(items), 2):
        row_id = f"ROW-{row_index // 2 + 1}"
        position["GRID_ID"]["children"].append(row_id)
        row_children = []
        for name, chart_id in items[row_index : row_index + 2]:
            chart_key = f"CHART-{chart_id}"
            row_children.append(chart_key)
            position[chart_key] = {
                "type": "CHART",
                "id": chart_key,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {"width": 6, "height": 50, "chartId": chart_id, "sliceName": name},
            }
        position[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": row_children,
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
    return position


def ensure_dashboard(api, chart_ids):
    existing = find_one(api, "dashboard", "slug", DASHBOARD_SLUG)
    if existing:
        api.call("DELETE", f"/api/v1/dashboard/{existing}")
    metadata = {
        "native_filter_configuration": [
            {
                "id": "NATIVE_FILTER-period-compare",
                "name": "Periodo",
                "filterType": "filter_period_compare",
                "targets": [{}],
                "controlValues": {"enableEmptyFilter": False},
                "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
                "cascadeParentIds": [],
                "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
                "type": "NATIVE_FILTER",
                "description": "",
            }
        ],
        "chart_configuration": {},
        "color_scheme": "",
        "refresh_frequency": 0,
        "expanded_slices": {},
        "label_colors": {},
        "timed_refresh_immune_slices": [],
        "default_filters": "{}",
        "shared_label_colors": {},
        "map_label_colors": {},
    }
    dash_id = api.call(
        "POST",
        "/api/v1/dashboard/",
        {
            "dashboard_title": DASHBOARD_TITLE,
            "slug": DASHBOARD_SLUG,
            "published": True,
            "position_json": json.dumps(build_position(chart_ids)),
            "json_metadata": json.dumps(metadata),
        },
    )["id"]
    for chart_id in chart_ids.values():
        api.call("PUT", f"/api/v1/chart/{chart_id}", {"dashboards": [dash_id]})
    return dash_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8088")
    parser.add_argument("--user", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--db-host", default="db-light", help="host di Postgres: db-light (compose light) o db (compose classico)")
    args = parser.parse_args()

    api = Api(args.base, args.user, args.password)
    db_id = ensure_database(api, args.db_host)
    sales_id = ensure_dataset(
        api,
        db_id,
        "sales_performance",
        "order_date",
        [
            {"metric_name": "count", "expression": "COUNT(*)"},
            {"metric_name": "sum_sales", "expression": "SUM(sales_amount)", "verbose_name": "Vendite"},
            {"metric_name": "orders", "expression": "SUM(order_count)", "verbose_name": "Ordini"},
        ],
    )

    flt = [time_filter("order_date")]
    charts = {
        f"{CHART_PREFIX} Table": ensure_chart(
            api, sales_id, f"{CHART_PREFIX} Table", "table",
            {"query_mode": "aggregate", "groupby": ["category"], "metrics": ["sum_sales", "orders"],
             "all_columns": [], "percent_metrics": [], "adhoc_filters": flt, "row_limit": 1000,
             "order_desc": True, "show_totals": False},
        ),
        f"{CHART_PREFIX} Big Number": ensure_chart(
            api, sales_id, f"{CHART_PREFIX} Big Number", "pop_kpi",
            {"metric": "sum_sales", "adhoc_filters": flt, "row_limit": 1000},
        ),
        f"{CHART_PREFIX} Line giorno": ensure_chart(
            api, sales_id, f"{CHART_PREFIX} Line giorno", "echarts_timeseries_line",
            {"x_axis": "order_date", "time_grain_sqla": "P1D", "metrics": ["sum_sales"], "groupby": [],
             "adhoc_filters": flt, "row_limit": 10000, "show_legend": True, "rich_tooltip": True},
        ),
        f"{CHART_PREFIX} Bar mese": ensure_chart(
            api, sales_id, f"{CHART_PREFIX} Bar mese", "echarts_timeseries_bar",
            {"x_axis": "order_date", "time_grain_sqla": "P1M", "metrics": ["sum_sales"], "groupby": [],
             "adhoc_filters": flt, "row_limit": 10000, "show_legend": True, "rich_tooltip": True},
        ),
        f"{CHART_PREFIX} Pivot": ensure_chart(
            api, sales_id, f"{CHART_PREFIX} Pivot", "pivot_table_v2",
            {"groupbyRows": ["category"], "groupbyColumns": ["region"], "metrics": ["sum_sales"],
             "aggregateFunction": "Sum", "metricsLayout": "COLUMNS", "adhoc_filters": flt,
             "row_limit": 10000},
        ),
    }
    dash_id = ensure_dashboard(api, charts)
    print(json.dumps({"database": db_id, "sales_dataset": sales_id, "charts": charts, "dashboard": dash_id,
                      "url": f"/superset/dashboard/{DASHBOARD_SLUG}/"}, indent=2))


if __name__ == "__main__":
    main()
