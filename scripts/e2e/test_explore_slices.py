import urllib.request
import urllib.parse
import http.cookiejar
import json
import re

BASE_URL = "http://localhost:8088"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Fetch login page
login_html = opener.open(f"{BASE_URL}/login/").read().decode("utf-8")
csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_html).group(1)

# 2. Login
data = urllib.parse.urlencode({"username": "admin", "password": "admin", "csrf_token": csrf}).encode("utf-8")
login_resp = opener.open(f"{BASE_URL}/login/", data=data)
print(f"Login status: {login_resp.getcode()}")

# 3. Check slices
slices = [
    (15, "kpi_comparison", "KPI Card Vendite"),
    (16, "kpi_comparison", "KPI Card Ordini"),
    (17, "hierarchical_table", "StratumTree"),
    (18, "stratum_bar", "StratumBar"),
    (19, "stratum_heatmap", "Stratum Heatmap"),
]

for sid, viz, name in slices:
    url = f"{BASE_URL}/explore/?slice_id={sid}"
    try:
        with opener.open(url, timeout=10) as r:
            code = r.getcode()
            body = r.read().decode("utf-8", errors="ignore")
            has_viz = viz in body
            print(f"Slice {sid} [{viz}] '{name}' -> HTTP {code} (viz present in bootstrap: {has_viz})")
    except Exception as e:
        print(f"Slice {sid} [{viz}] '{name}' -> ERROR: {e}")

# 4. Check Dashboard
dash_url = f"{BASE_URL}/superset/dashboard/collaudo-confronto-temporale/"
try:
    with opener.open(dash_url, timeout=10) as r:
        code = r.getcode()
        body = r.read().decode("utf-8", errors="ignore")
        print(f"\nDashboard URL: {dash_url} -> HTTP {code} (Length: {len(body)} bytes)")
except Exception as e:
    print(f"\nDashboard ERROR: {e}")

# 5. Check API Chart 15
with opener.open(f"{BASE_URL}/api/v1/chart/15") as r:
    c15 = json.loads(r.read().decode("utf-8")).get("result", {})
    print(f"\nAPI Chart 15: name='{c15.get('slice_name')}', viz_type='{c15.get('viz_type')}'")
    params = json.loads(c15.get("params", "{}"))
    dataset_id = int(params.get("datasource", "1__table").split("__")[0])

# 6. Test /api/v1/chart/data for Chart 15
query_context = {
    "datasource": {"id": dataset_id, "type": "table"},
    "force": False,
    "queries": [
        {
            "filters": [
                {
                    "col": "order_date",
                    "op": "TEMPORAL_RANGE",
                    "val": "2026-09-01 : 2026-10-01"
                }
            ],
            "metrics": ["sum_sales"],
            "time_offsets": ["2026-08-01 : 2026-09-01"]
        }
    ],
    "result_format": "json",
    "result_type": "full"
}

headers = {"Content-Type": "application/json", "X-CSRFToken": csrf}
req = urllib.request.Request(f"{BASE_URL}/api/v1/chart/data", data=json.dumps(query_context).encode("utf-8"), headers=headers)
try:
    with opener.open(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        rows = res.get("result", [{}])[0].get("data", [])
        print(f"\nChart 15 /api/v1/chart/data response: {rows}")
except Exception as e:
    print(f"\nChart 15 /api/v1/chart/data ERROR: {e}")

# 7. Test /api/v1/chart/data for Stratum Heatmap (Chart 19)
query_heatmap = {
    "datasource": {"id": dataset_id, "type": "table"},
    "force": False,
    "queries": [
        {
            "columns": ["category", "region"],
            "filters": [
                {
                    "col": "order_date",
                    "op": "TEMPORAL_RANGE",
                    "val": "2026-09-01 : 2026-10-01"
                }
            ],
            "metrics": ["sum_sales"],
            "time_offsets": ["2026-08-01 : 2026-09-01"],
            "row_limit": 5
        }
    ],
    "result_format": "json",
    "result_type": "full"
}

req_hm = urllib.request.Request(f"{BASE_URL}/api/v1/chart/data", data=json.dumps(query_heatmap).encode("utf-8"), headers=headers)
try:
    with opener.open(req_hm) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        rows = res.get("result", [{}])[0].get("data", [])
        print(f"\nChart 19 Stratum Heatmap rows (first 3):")
        for r in rows[:3]:
            print(" ", r)
except Exception as e:
    print(f"\nChart 19 ERROR: {e}")



