#!/usr/bin/env python3
"""
Sets up the dedicated dashboard featuring the custom plugins:
1. kpi_comparison (KPI Card with clear Delta, % Badge, and Comparison Period)
2. hierarchical_table (StratumTree Matrix Grid with expandable drilldown and variance badges)
3. stratum_bar (3D Isometric and Advanced Comparison Bar Chart)
4. stratum_heatmap (Stratum Heatmap Density Matrix)
"""

import http.cookiejar
import json
import sys
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:8088"
DASH_SLUG = "collaudo-confronto-temporale"
DASH_TITLE = "Dashboard Collaudo - Confronto Temporale (Plugin Personalizzati)"

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

    dataset_id = api.find_one("dataset", "table_name", "sales_performance")
    if not dataset_id:
        print("Dataset 'sales_performance' not found.")
        sys.exit(1)

    flt = [{
        "expressionType": "SIMPLE",
        "subject": "order_date",
        "operator": "TEMPORAL_RANGE",
        "comparator": "No filter",
        "clause": "WHERE"
    }]

    charts_spec = [
        {
            "name": "KPI Card Vendite (KPI Comparison)",
            "viz_type": "kpi_comparison",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "kpi_comparison",
                "metric": "sum_sales",
                "adhoc_filters": flt,
                "enable_comparison": True,
                "kpi_title": "Totale Vendite",
                "show_title": True,
                "kpi_subtitle": "Periodo Riferimento vs Periodo Confronto",
                "comparison_label": "vs Mese Precedente",
                "prefix_value": "€ ",
                "number_format": "$,.2f",
                "badge_style": "pill",
                "card_box_shadow": "subtle",
                "card_border_radius": "rounded"
            }
        },
        {
            "name": "KPI Card Ordini (KPI Comparison)",
            "viz_type": "kpi_comparison",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "kpi_comparison",
                "metric": "orders",
                "adhoc_filters": flt,
                "enable_comparison": True,
                "kpi_title": "Numero Ordini",
                "show_title": True,
                "kpi_subtitle": "Periodo Riferimento vs Periodo Confronto",
                "comparison_label": "vs Mese Precedente",
                "prefix_value": "",
                "number_format": "SMART_NUMBER",
                "badge_style": "pill",
                "card_box_shadow": "subtle",
                "card_border_radius": "rounded"
            }
        },
        {
            "name": "Matrice Gerarchica Categoria e Regione (StratumTree)",
            "viz_type": "hierarchical_table",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "hierarchical_table",
                "hierarchyType": "multi_dimension",
                "groupby": ["category", "region"],
                "metrics": ["sum_sales", "orders"],
                "adhoc_filters": flt,
                "row_limit": 1000
            }
        },
        {
            "name": "Confronto Barre per Categoria (StratumBar)",
            "viz_type": "stratum_bar",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "stratum_bar",
                "x_axis": "category",
                "metrics": ["sum_sales"],
                "groupby": [],
                "adhoc_filters": flt,
                "row_limit": 1000,
                "show_legend": True
            }
        },
        {
            "name": "Mappa Termica Densità Categoria x Regione (Stratum Heatmap)",
            "viz_type": "stratum_heatmap",
            "params": {
                "datasource": f"{dataset_id}__table",
                "viz_type": "stratum_heatmap",
                "xAxisDimension": "category",
                "yAxisDimension": "region",
                "metric": "sum_sales",
                "adhoc_filters": flt,
                "showValues": True,
                "showRowTotals": True,
                "showColumnTotals": True
            }
        }
    ]

    chart_ids = {}
    for spec in charts_spec:
        c_name = spec["name"]
        existing_id = api.find_one("chart", "slice_name", c_name)
        if existing_id:
            api.call("PUT", f"/api/v1/chart/{existing_id}", {
                "slice_name": c_name,
                "viz_type": spec["viz_type"],
                "params": json.dumps(spec["params"])
            })
            chart_ids[c_name] = existing_id
            print(f"Updated chart '{c_name}' (ID {existing_id})")
        else:
            new_id = api.call("POST", "/api/v1/chart/", {
                "slice_name": c_name,
                "viz_type": spec["viz_type"],
                "datasource_id": dataset_id,
                "datasource_type": "table",
                "params": json.dumps(spec["params"])
            })["id"]
            chart_ids[c_name] = new_id
            print(f"Created chart '{c_name}' (ID {new_id})")

    c_list = list(chart_ids.values())
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["HEADER_ID", "ROW-KPIS", "ROW-TREE", "ROW-CHARTS"], "parents": ["ROOT_ID"]},
        "HEADER_ID": {
            "type": "HEADER",
            "id": "HEADER_ID",
            "meta": {"text": DASH_TITLE},
            "parents": ["ROOT_ID", "GRID_ID"]
        },
        "ROW-KPIS": {
            "type": "ROW",
            "id": "ROW-KPIS",
            "children": [f"CHART-{c_list[0]}", f"CHART-{c_list[1]}"],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        },
        f"CHART-{c_list[0]}": {
            "type": "CHART",
            "id": f"CHART-{c_list[0]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-KPIS"],
            "meta": {"width": 6, "height": 38, "chartId": c_list[0], "sliceName": charts_spec[0]["name"]}
        },
        f"CHART-{c_list[1]}": {
            "type": "CHART",
            "id": f"CHART-{c_list[1]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-KPIS"],
            "meta": {"width": 6, "height": 38, "chartId": c_list[1], "sliceName": charts_spec[1]["name"]}
        },
        "ROW-TREE": {
            "type": "ROW",
            "id": "ROW-TREE",
            "children": [f"CHART-{c_list[2]}"],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        },
        f"CHART-{c_list[2]}": {
            "type": "CHART",
            "id": f"CHART-{c_list[2]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-TREE"],
            "meta": {"width": 12, "height": 60, "chartId": c_list[2], "sliceName": charts_spec[2]["name"]}
        },
        "ROW-CHARTS": {
            "type": "ROW",
            "id": "ROW-CHARTS",
            "children": [f"CHART-{c_list[3]}", f"CHART-{c_list[4]}"],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        },
        f"CHART-{c_list[3]}": {
            "type": "CHART",
            "id": f"CHART-{c_list[3]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-CHARTS"],
            "meta": {"width": 6, "height": 55, "chartId": c_list[3], "sliceName": charts_spec[3]["name"]}
        },
        f"CHART-{c_list[4]}": {
            "type": "CHART",
            "id": f"CHART-{c_list[4]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", "ROW-CHARTS"],
            "meta": {"width": 6, "height": 55, "chartId": c_list[4], "sliceName": charts_spec[4]["name"]}
        }
    }

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
                "description": "Filtro nativo PeriodCompare senza prodotto cartesiano"
            }
        ],
        "chart_configuration": {},
        "color_scheme": "supersetColors",
        "refresh_frequency": 0
    }

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
        print(f"Updated Dashboard ID {dash_id}")
    else:
        dash_id = api.call("POST", "/api/v1/dashboard/", dash_payload)["id"]
        print(f"Created Dashboard ID {dash_id}")

    for cid in c_list:
        api.call("PUT", f"/api/v1/chart/{cid}", {"dashboards": [dash_id]})

    dash_url = f"{BASE_URL}/superset/dashboard/{DASH_SLUG}/"
    print(f"\nDashboard aggiornata con successo con i plugin personalizzati:")
    print(f"-> {dash_url}\n")

if __name__ == "__main__":
    main()
