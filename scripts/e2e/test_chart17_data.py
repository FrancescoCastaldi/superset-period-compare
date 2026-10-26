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

headers = {'Content-Type': 'application/json', 'X-CSRFToken': csrf}

# Query chart 17 params
with opener.open('http://localhost:8088/api/v1/chart/17') as r:
    c17 = json.loads(r.read().decode('utf-8'))['result']
    print("Chart 17 params:", json.dumps(json.loads(c17['params']), indent=2))

qc = {
    'datasource': {'id': 1, 'type': 'table'},
    'force': False,
    'queries': [
        {
            'columns': ['category', 'region'],
            'filters': [{'col': 'order_date', 'op': 'TEMPORAL_RANGE', 'val': '2026-09-01 : 2026-10-01'}],
            'metrics': ['sum_sales', 'orders'],
            'time_offsets': ['2026-08-01 : 2026-09-01'],
            'row_limit': 10
        }
    ],
    'result_format': 'json',
    'result_type': 'full'
}
req = urllib.request.Request('http://localhost:8088/api/v1/chart/data', data=json.dumps(qc).encode('utf-8'), headers=headers)
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print("Chart 17 data with time_offsets (first 3 rows):")
    print(json.dumps(res['result'][0]['data'][:3], indent=2))
