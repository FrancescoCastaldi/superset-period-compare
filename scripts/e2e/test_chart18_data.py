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

# Query chart 18 params
with opener.open('http://localhost:8088/api/v1/chart/18') as r:
    c18 = json.loads(r.read().decode('utf-8'))['result']
    print("Chart 18 params:", json.dumps(json.loads(c18['params']), indent=2))

qc = {
    'datasource': {'id': 1, 'type': 'table'},
    'force': False,
    'queries': [
        {
            'columns': ['category'],
            'filters': [{'col': 'order_date', 'op': 'TEMPORAL_RANGE', 'val': '2026-09-01 : 2026-10-01'}],
            'metrics': ['sum_sales'],
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
    print("Chart 18 data with time_offsets:")
    print(json.dumps(res['result'][0]['data'], indent=2))
