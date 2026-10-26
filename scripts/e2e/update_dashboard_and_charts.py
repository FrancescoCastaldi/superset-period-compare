import http.cookiejar
import json
import re
import urllib.parse
import urllib.request

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login
login_html = opener.open('http://localhost:8088/login/').read().decode('utf-8')
csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_html).group(1)
data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin', 'csrf_token': csrf}).encode('utf-8')
opener.open('http://localhost:8088/login/', data=data)

headers = {'Content-Type': 'application/json', 'X-CSRFToken': csrf}

# 2. Update Chart 17 params (StratumTree) to enable showVarianceDelta
res_c17 = opener.open('http://localhost:8088/api/v1/chart/17').read().decode('utf-8')
c17 = json.loads(res_c17)['result']
params17 = json.loads(c17['params'])
params17['showVarianceDelta'] = True
params17['initialExpandDepth'] = 1
params17['stripedRows'] = True

put_c17 = {
    'params': json.dumps(params17),
    'dashboards': [3]
}
req17 = urllib.request.Request(
    'http://localhost:8088/api/v1/chart/17',
    data=json.dumps(put_c17).encode('utf-8'),
    headers=headers,
    method='PUT'
)
with opener.open(req17) as r:
    print("Updated Chart 17 (StratumTree):", r.status)

# 3. Attach Chart 20 (Calendar Filter) to Dashboard 3
put_c20 = {
    'dashboards': [3]
}
req20 = urllib.request.Request(
    'http://localhost:8088/api/v1/chart/20',
    data=json.dumps(put_c20).encode('utf-8'),
    headers=headers,
    method='PUT'
)
with opener.open(req20) as r:
    print("Attached Chart 20 to Dashboard 3:", r.status)

# 4. Ensure Charts 11, 12, 13, 14 are disconnected
for orphan_id in [11, 12, 13, 14]:
    req_orphan = urllib.request.Request(
        f'http://localhost:8088/api/v1/chart/{orphan_id}',
        data=json.dumps({'dashboards': []}).encode('utf-8'),
        headers=headers,
        method='PUT'
    )
    with opener.open(req_orphan) as r:
        print(f"Disconnected orphan chart {orphan_id}:", r.status)

# 5. Fetch Dashboard 3 and update position_json & json_metadata
res_d3 = opener.open('http://localhost:8088/api/v1/dashboard/3').read().decode('utf-8')
d3 = json.loads(res_d3)['result']
meta = json.loads(d3['json_metadata'])
meta['filter_bar_orientation'] = 'HORIZONTAL'

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
            "ROW-CALENDAR",
            "ROW-KPIS",
            "ROW-TREE",
            "ROW-CHARTS"
        ],
        "parents": [
            "ROOT_ID"
        ]
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
    'position_json': json.dumps(pos),
    'json_metadata': json.dumps(meta)
}

req_dash = urllib.request.Request(
    'http://localhost:8088/api/v1/dashboard/3',
    data=json.dumps(put_d3).encode('utf-8'),
    headers=headers,
    method='PUT'
)
with opener.open(req_dash) as r:
    print("Updated Dashboard 3 layout and metadata:", r.status)

print("\nDashboard update complete!")
