import http.cookiejar
import json
import re
import urllib.parse
import urllib.request

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
html = opener.open('http://localhost:8088/login/').read().decode('utf-8')
csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin', 'csrf_token': csrf}).encode('utf-8')
opener.open('http://localhost:8088/login/', data=data)

headers = {"Content-Type": "application/json", "X-CSRFToken": csrf}

# Test querying /api/v1/chart/data with calendar_filter query context
qc = {
    "datasource": {"id": 1, "type": "table"},
    "force": False,
    "queries": [
        {
            "columns": ["order_date"],
            "metrics": ["sum_sales"],
            "filters": [],
            "row_limit": 1000
        }
    ],
    "result_format": "json",
    "result_type": "full"
}

req = urllib.request.Request('http://localhost:8088/api/v1/chart/data', data=json.dumps(qc).encode('utf-8'), headers=headers)
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    data = res.get('result', [{}])[0].get('data', [])
    print(f"Calendar query returned {len(data)} rows. First 3:")
    print(data[:3])
