import http.cookiejar
import json
import re
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:8088"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login
login_html = opener.open(f"{BASE_URL}/login/").read().decode("utf-8")
csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_html).group(1)
data = urllib.parse.urlencode({"username": "admin", "password": "admin", "csrf_token": csrf}).encode("utf-8")
opener.open(f"{BASE_URL}/login/", data=data)
headers = {"Content-Type": "application/json", "X-CSRFToken": csrf}

# 2. Update Chart 15 (KPI Vendite)
res_c15 = opener.open(f"{BASE_URL}/api/v1/chart/15").read().decode("utf-8")
c15 = json.loads(res_c15)["result"]
params15 = json.loads(c15["params"])
params15["kpi_title"] = "Totale Vendite"
params15["kpi_subtitle"] = "Tempo 1 (Settembre 2026) vs Tempo 2 (Agosto 2026)"
params15["comparison_label"] = "vs Tempo 2 (Agosto 2026)"
req15 = urllib.request.Request(
    f"{BASE_URL}/api/v1/chart/15",
    data=json.dumps({"params": json.dumps(params15), "dashboards": [3]}).encode("utf-8"),
    headers=headers,
    method="PUT"
)
with opener.open(req15) as r:
    print(f"Updated Chart 15 (KPI Vendite): HTTP {r.status}")

# 3. Update Chart 16 (KPI Ordini)
res_c16 = opener.open(f"{BASE_URL}/api/v1/chart/16").read().decode("utf-8")
c16 = json.loads(res_c16)["result"]
params16 = json.loads(c16["params"])
params16["kpi_title"] = "Numero Ordini"
params16["kpi_subtitle"] = "Tempo 1 (Settembre 2026) vs Tempo 2 (Agosto 2026)"
params16["comparison_label"] = "vs Tempo 2 (Agosto 2026)"
req16 = urllib.request.Request(
    f"{BASE_URL}/api/v1/chart/16",
    data=json.dumps({"params": json.dumps(params16), "dashboards": [3]}).encode("utf-8"),
    headers=headers,
    method="PUT"
)
with opener.open(req16) as r:
    print(f"Updated Chart 16 (KPI Ordini): HTTP {r.status}")

# 4. Update Chart 20 (Calendar Filter)
res_c20 = opener.open(f"{BASE_URL}/api/v1/chart/20").read().decode("utf-8")
c20 = json.loads(res_c20)["result"]
params20 = json.loads(c20["params"])
params20["default_value_mode"] = "custom"
params20["custom_default_start_date"] = "2026-09-01"
params20["custom_default_end_date"] = "2026-09-30"
params20["customDefaultStartDate"] = "2026-09-01"
params20["customDefaultEndDate"] = "2026-09-30"
params20["default_view_year"] = 2026
params20["default_view_month"] = 9
params20["defaultViewYear"] = 2026
params20["defaultViewMonth"] = 9
req20 = urllib.request.Request(
    f"{BASE_URL}/api/v1/chart/20",
    data=json.dumps({"params": json.dumps(params20), "dashboards": [3]}).encode("utf-8"),
    headers=headers,
    method="PUT"
)
with opener.open(req20) as r:
    print(f"Updated Chart 20 (Calendar Filter): HTTP {r.status}")

# 5. Fetch Dashboard 3 and configure prominent Banner
res_d3 = opener.open(f"{BASE_URL}/api/v1/dashboard/3").read().decode("utf-8")
d3 = json.loads(res_d3)["result"]
meta = json.loads(d3["json_metadata"])
meta["filter_bar_orientation"] = "HORIZONTAL"

banner_markdown = """### ⏱️ Quadro Sinottico: Confronto Temporale (Tempo 1 vs Tempo 2)

> 🔵 `TEMPO 1` **Periodo di Riferimento Attivo**: **Settembre 2026** (`01/09/2026 - 30/09/2026`, 30 giorni), analisi primaria corrente  
> 🟣 `TEMPO 2` **Periodo di Confronto (Benchmark)**: **Agosto 2026** (`01/08/2026 - 31/08/2026`, 31 giorni), benchmark storico precedente  
> ⚖️ `CALCOLO DIFFERENZIALE` **Regola Scostamento**: **Scostamento = Tempo 1 - Tempo 2**, formula variazione `Δ% = ((Tempo 1 - Tempo 2) / Tempo 2) * 100`
"""

pos = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {
        "type": "ROOT",
        "id": "ROOT_ID",
        "children": [
            "GRID_ID"
        ]
    },
    "GRID_ID": {
        "type": "GRID",
        "id": "GRID_ID",
        "children": [
            "ROW-BANNER",
            "ROW-CALENDAR",
            "ROW-KPIS",
            "ROW-TREE",
            "ROW-CHARTS"
        ],
        "parents": [
            "ROOT_ID"
        ]
    },
    "ROW-BANNER": {
        "type": "ROW",
        "id": "ROW-BANNER",
        "children": [
            "MARKDOWN-banner"
        ],
        "parents": [
            "ROOT_ID",
            "GRID_ID"
        ],
        "meta": {
            "background": "BACKGROUND_TRANSPARENT"
        }
    },
    "MARKDOWN-banner": {
        "type": "MARKDOWN",
        "id": "MARKDOWN-banner",
        "children": [],
        "parents": [
            "ROOT_ID",
            "GRID_ID",
            "ROW-BANNER"
        ],
        "meta": {
            "width": 12,
            "height": 22,
            "code": banner_markdown
        }
    },
    "ROW-CALENDAR": {
        "type": "ROW",
        "id": "ROW-CALENDAR",
        "children": [
            "CHART-20"
        ],
        "parents": [
            "ROOT_ID",
            "GRID_ID"
        ],
        "meta": {
            "background": "BACKGROUND_TRANSPARENT"
        }
    },
    "CHART-20": {
        "type": "CHART",
        "id": "CHART-20",
        "children": [],
        "parents": [
            "ROOT_ID",
            "GRID_ID",
            "ROW-CALENDAR"
        ],
        "meta": {
            "width": 12,
            "height": 54,
            "chartId": 20,
            "sliceName": "Filtro Calendario (Calendar Filter)"
        }
    },
    "ROW-KPIS": {
        "type": "ROW",
        "id": "ROW-KPIS",
        "children": [
            "CHART-15",
            "CHART-16"
        ],
        "parents": [
            "ROOT_ID",
            "GRID_ID"
        ],
        "meta": {
            "background": "BACKGROUND_TRANSPARENT"
        }
    },
    "CHART-15": {
        "type": "CHART",
        "id": "CHART-15",
        "children": [],
        "parents": [
            "ROOT_ID",
            "GRID_ID",
            "ROW-KPIS"
        ],
        "meta": {
            "width": 6,
            "height": 38,
            "chartId": 15,
            "sliceName": "KPI Card Vendite (KPI Comparison)"
        }
    },
    "CHART-16": {
        "type": "CHART",
        "id": "CHART-16",
        "children": [],
        "parents": [
            "ROOT_ID",
            "GRID_ID",
            "ROW-KPIS"
        ],
        "meta": {
            "width": 6,
            "height": 38,
            "chartId": 16,
            "sliceName": "KPI Card Ordini (KPI Comparison)"
        }
    },
    "ROW-TREE": {
        "type": "ROW",
        "id": "ROW-TREE",
        "children": [
            "CHART-17"
        ],
        "parents": [
            "ROOT_ID",
            "GRID_ID"
        ],
        "meta": {
            "background": "BACKGROUND_TRANSPARENT"
        }
    },
    "CHART-17": {
        "type": "CHART",
        "id": "CHART-17",
        "children": [],
        "parents": [
            "ROOT_ID",
            "GRID_ID",
            "ROW-TREE"
        ],
        "meta": {
            "width": 12,
            "height": 62,
            "chartId": 17,
            "sliceName": "Matrice Gerarchica Categoria e Regione (StratumTree)"
        }
    },
    "ROW-CHARTS": {
        "type": "ROW",
        "id": "ROW-CHARTS",
        "children": [
            "CHART-18",
            "CHART-19"
        ],
        "parents": [
            "ROOT_ID",
            "GRID_ID"
        ],
        "meta": {
            "background": "BACKGROUND_TRANSPARENT"
        }
    },
    "CHART-18": {
        "type": "CHART",
        "id": "CHART-18",
        "children": [],
        "parents": [
            "ROOT_ID",
            "GRID_ID",
            "ROW-CHARTS"
        ],
        "meta": {
            "width": 6,
            "height": 62,
            "chartId": 18,
            "sliceName": "Confronto Barre per Categoria (StratumBar)"
        }
    },
    "CHART-19": {
        "type": "CHART",
        "id": "CHART-19",
        "children": [],
        "parents": [
            "ROOT_ID",
            "GRID_ID",
            "ROW-CHARTS"
        ],
        "meta": {
            "width": 6,
            "height": 62,
            "chartId": 19,
            "sliceName": "Mappa Termica Densità Categoria x Regione (Stratum Heatmap)"
        }
    }
}

put_d3 = {
    "position_json": json.dumps(pos),
    "json_metadata": json.dumps(meta)
}

req_dash = urllib.request.Request(
    f"{BASE_URL}/api/v1/dashboard/3",
    data=json.dumps(put_d3).encode("utf-8"),
    headers=headers,
    method="PUT"
)
with opener.open(req_dash) as r:
    print(f"Updated Dashboard 3 layout and metadata: HTTP {r.status}")

print("\nDashboard update complete!")
