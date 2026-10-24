#!/usr/bin/env python3
"""
Creates a clear, dedicated showcase dashboard demonstrating the PeriodCompare
architecture live in Apache Superset without Cartesian product views.
"""

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:8088"
DASH_SLUG = "collaudo-confronto-temporale"
DASH_TITLE = "Dashboard Collaudo - Confronto Temporale (PeriodCompare)"

class SupersetApi:
    def __init__(self, base, user, password):
        self.base = base.rstrip("/")
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        
        login_res = self.call("POST", "/api/v1/security/login", {
            "username": user,
            "password": password,
            "provider": "db",
            "refresh": True
        })
        self.token = login_res["access_token"]
        csrf_res = self.call("GET", "/api/v1/security/csrf_token/")
        self.csrf = csrf_res["result"]

    def call(self, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json", "Referer": self.base}
        if hasattr(self, "token") and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if hasattr(self, "csrf") and self.csrf:
            headers["X-CSRFToken"] = self.csrf
            
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            err_msg = exc.read().decode("utf-8")
            print(f"[API ERROR] {method} {path} -> HTTP {exc.code}: {err_msg[:300]}")
            raise

    def find_one(self, resource, col, val):
        q = json.dumps({"filters": [{"col": col, "opr": "eq", "value": val}]})
        res = self.call("GET", f"/api/v1/{resource}/?q={urllib.parse.quote(q)}")
        items = res.get("result", [])
        return items[0]["id"] if items else None

def main():
    api = SupersetApi(BASE_URL, "admin", "admin")
    print(f"Connected to Superset at {BASE_URL}")

    # 1. Dataset sales_performance
    dataset_id = api.find_one("dataset", "table_name", "sales_performance")
    if not dataset_id:
        print("Dataset 'sales_performance' not found. Please run setup-test-dashboard.py first.")
        sys.exit(1)
    print(f"Using dataset sales_performance (ID {dataset_id})")

    # Time filter definition
    flt = [{
        "expressionType": "SIMPLE",
        "subject": "order_date",
        "operator": "TEMPORAL_RANGE",
        "comparator": "No filter",
        "clause": "WHERE"
    }]

    # 2. Charts definition
    charts_spec = [
        {
            "name": "KPI Totale Vendite (Settembre vs Agosto)",
            "viz_type": "big_number_total",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "big_number_total",
                "metric": "sum_sales",
                "adhoc_filters": flt,
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
                "y_axis_format": "$,.2f",
                "time_format": "smart_date"
            }
        },
        {
            "name": "Tabella Categorie (Vendite e Ordini con Confronto)",
            "viz_type": "table",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "table",
                "query_mode": "aggregate",
                "groupby": ["category"],
                "metrics": ["sum_sales", "orders"],
                "all_columns": [],
                "percent_metrics": [],
                "adhoc_filters": flt,
                "row_limit": 100,
                "order_desc": True,
                "show_totals": True
            }
        },
        {
            "name": "Trend Temporale Giornaliero (Line Series)",
            "viz_type": "echarts_timeseries_line",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "echarts_timeseries_line",
                "x_axis": "order_date",
                "time_grain_sqla": "P1D",
                "metrics": ["sum_sales"],
                "groupby": [],
                "adhoc_filters": flt,
                "row_limit": 1000,
                "show_legend": True,
                "rich_tooltip": True
            }
        },
        {
            "name": "Confronto Mensile per Categoria (Bar Series)",
            "viz_type": "echarts_timeseries_bar",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "order_date",
                "time_grain_sqla": "P1M",
                "metrics": ["sum_sales"],
                "groupby": ["category"],
                "adhoc_filters": flt,
                "row_limit": 1000,
                "show_legend": True,
                "rich_tooltip": True
            }
        }
    ]

    created_chart_ids = {}
    for spec in charts_spec:
        c_name = spec["name"]
        existing_id = api.find_one("chart", "slice_name", c_name)
        if existing_id:
            api.call("PUT", f"/api/v1/chart/{existing_id}", {
                "slice_name": c_name,
                "viz_type": spec["viz_type"],
                "params": json.dumps(spec["params"])
            })
            created_chart_ids[c_name] = existing_id
            print(f"Updated chart '{c_name}' (ID {existing_id})")
        else:
            new_id = api.call("POST", "/api/v1/chart/", {
                "slice_name": c_name,
                "viz_type": spec["viz_type"],
                "datasource_id": dataset_id,
                "datasource_type": "table",
                "params": json.dumps(spec["params"])
            })["id"]
            created_chart_ids[c_name] = new_id
            print(f"Created chart '{c_name}' (ID {new_id})")

    # 3. Build position layout
    chart_list = list(created_chart_ids.values())
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["HEADER_ID", "ROW-1", "ROW-2"], "parents": ["ROOT_ID"]},
        "HEADER_ID": {
            "type": "HEADER",
            "id": "HEADER_ID",
            "meta": {"text": DASH_TITLE},
            "parents": ["ROOT_ID", "GRID_ID"]
        },
        "ROW-1": {
            "type": "ROW",
            "id": "ROW-1",
            "children": [f"CHART-{chart_list[0]}", f"CHART-{chart_list[1]}"],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        },
        f"CHART-{chart_list[0]}": {
            "type": "CHART",
            "id": f"CHART-{chart_list[0]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-1"],
            "meta": {"width": 4, "height": 50, "chartId": chart_list[0], "sliceName": charts_spec[0]["name"]}
        },
        f"CHART-{chart_list[1]}": {
            "type": "CHART",
            "id": f"CHART-{chart_list[1]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-1"],
            "meta": {"width": 8, "height": 50, "chartId": chart_list[1], "sliceName": charts_spec[1]["name"]}
        },
        "ROW-2": {
            "type": "ROW",
            "id": "ROW-2",
            "children": [f"CHART-{chart_list[2]}", f"CHART-{chart_list[3]}"],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        },
        f"CHART-{chart_list[2]}": {
            "type": "CHART",
            "id": f"CHART-{chart_list[2]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-2"],
            "meta": {"width": 6, "height": 50, "chartId": chart_list[2], "sliceName": charts_spec[2]["name"]}
        },
        f"CHART-{chart_list[3]}": {
            "type": "CHART",
            "id": f"CHART-{chart_list[3]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-2"],
            "meta": {"width": 6, "height": 50, "chartId": chart_list[3], "sliceName": charts_spec[3]["name"]}
        }
    }

    # 4. Native filter PeriodCompare definition
    ref_range = "2026-09-01 : 2026-10-01"
    comp_range = "2026-08-01 : 2026-09-01"
    metadata = {
        "native_filter_configuration": [
            {
                "id": "NATIVE_FILTER-period-compare",
                "name": "Periodo & Confronto Temporale",
                "filterType": "filter_period_compare",
                "targets": [{}],
                "controlValues": {"enableEmptyFilter": False},
                "defaultDataMask": {
                    "extraFormData": {
                        "time_range": ref_range,
                        "time_compare": [comp_range],
                        "comparison_type": "values"
                    },
                    "filterState": {
                        "value": {
                            "referenceRange": ref_range,
                            "comparisonMode": "custom",
                            "customRange": comp_range,
                            "comparisonType": "values"
                        },
                        "label": ref_range
                    },
                    "ownState": {}
                },
                "cascadeParentIds": [],
                "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
                "type": "NATIVE_FILTER",
                "description": "Filtro nativo per periodo di riferimento e periodo di confronto senza prodotto cartesiano"
            }
        ],
        "chart_configuration": {},
        "color_scheme": "supersetColors",
        "refresh_frequency": 0
    }

    # 5. Create or update dashboard
    dash_id = api.find_one("dashboard", "slug", DASH_SLUG)
    dash_payload = {
        "dashboard_title": DASH_TITLE,
        "slug": DASH_SLUG,
        "published": True,
        "position_json": json.dumps(position),
        "json_metadata": json.dumps(metadata)
    }

    if dash_id:
        api.call("PUT", f"/api/v1/dashboard/{dash_id}", dash_payload)
        print(f"Updated Dashboard '{DASH_TITLE}' (ID {dash_id})")
    else:
        dash_id = api.call("POST", "/api/v1/dashboard/", dash_payload)["id"]
        print(f"Created Dashboard '{DASH_TITLE}' (ID {dash_id})")

    # Link charts to dashboard
    for cid in chart_list:
        api.call("PUT", f"/api/v1/chart/{cid}", {"dashboards": [dash_id]})

    dash_url = f"{BASE_URL}/superset/dashboard/{DASH_SLUG}/"
    print(f"\n=======================================================")
    print(f"DASHBOARD PRONTA ALL'USO: {dash_url}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
