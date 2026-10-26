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

qc = {
    'datasource': {'id': 1, 'type': 'table'},
    'force': False,
    'queries': [
        {
            'columns': ['category', 'region'],
            'filters': [{'col': 'order_date', 'op': 'TEMPORAL_RANGE', 'val': '2026-09-01 : 2026-10-01'}],
            'metrics': ['sum_sales', 'orders'],
            'time_offsets': ['2026-08-01 : 2026-09-01'],
            'row_limit': 1000
        }
    ],
    'result_format': 'json',
    'result_type': 'full'
}
req = urllib.request.Request('http://localhost:8088/api/v1/chart/data', data=json.dumps(qc).encode('utf-8'), headers=headers)
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    rows = res['result'][0]['data']

# Aggregate by category and total
cats = {}
tot_curr_sales = 0
tot_comp_sales = 0
comp_key_sales = [k for k in rows[0].keys() if k.startswith('sum_sales__')][0]
comp_key_orders = [k for k in rows[0].keys() if k.startswith('orders__')][0]

for r in rows:
    c = r['category']
    if c not in cats:
        cats[c] = {'curr_sales': 0, 'comp_sales': 0, 'curr_orders': 0, 'comp_orders': 0}
    cats[c]['curr_sales'] += r.get('sum_sales') or 0
    cats[c]['comp_sales'] += r.get(comp_key_sales) or 0
    cats[c]['curr_orders'] += r.get('orders') or 0
    cats[c]['comp_orders'] += r.get(comp_key_orders) or 0
    tot_curr_sales += r.get('sum_sales') or 0
    tot_comp_sales += r.get(comp_key_sales) or 0

print("Category Summaries:")
for c, d in cats.items():
    delta = d['curr_sales'] - d['comp_sales']
    pct = (delta / d['comp_sales']) * 100 if d['comp_sales'] else 0
    print(f" {c:15}: Attuale={d['curr_sales']:10.2f}, Confronto={d['comp_sales']:10.2f}, Delta={delta:10.2f}, Delta%={pct:6.2f}%")

delta_tot = tot_curr_sales - tot_comp_sales
pct_tot = (delta_tot / tot_comp_sales) * 100 if tot_comp_sales else 0
print(f"\n Grand Total    : Attuale={tot_curr_sales:10.2f}, Confronto={tot_comp_sales:10.2f}, Delta={delta_tot:10.2f}, Delta%={pct_tot:6.2f}%")
