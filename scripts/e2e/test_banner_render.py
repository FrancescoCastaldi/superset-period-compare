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

# 2. Fetch Dashboard 3
res_d3 = opener.open(f"{BASE_URL}/api/v1/dashboard/3").read().decode("utf-8")
d3 = json.loads(res_d3)["result"]
pos = json.loads(d3["position_json"])

banner_table = """### ⏱️ Quadro Sinottico: Confronto Temporale (Tempo 1 vs Tempo 2)

| Periodo Temporale | Mese e Date (30 / 31 gg) | Ruolo di Analisi | Formula Differenziale |
| :--- | :--- | :--- | :--- |
| 🔵 **Tempo 1** | **Settembre 2026** (`01/09/2026 - 30/09/2026`) | **Periodo Riferimento Attivo** | **Scostamento = Tempo 1 - Tempo 2** |
| 🟣 **Tempo 2** | **Agosto 2026** (`01/08/2026 - 31/08/2026`) | **Periodo Confronto (Benchmark)** | `Δ% = ((Tempo 1 - Tempo 2) / Tempo 2) * 100` |
"""

pos["MARKDOWN-banner"]["meta"]["code"] = banner_table
pos["MARKDOWN-banner"]["meta"]["height"] = 24

put_d3 = {
    "position_json": json.dumps(pos),
    "json_metadata": d3["json_metadata"]
}

req_dash = urllib.request.Request(
    f"{BASE_URL}/api/v1/dashboard/3",
    data=json.dumps(put_d3).encode("utf-8"),
    headers=headers,
    method="PUT"
)
with opener.open(req_dash) as r:
    print(f"Updated Dashboard 3 banner: HTTP {r.status}")
