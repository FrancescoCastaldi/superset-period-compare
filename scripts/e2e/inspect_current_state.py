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

res = opener.open('http://localhost:8088/api/v1/dashboard/3').read().decode('utf-8')
d3 = json.loads(res)['result']
print('Dashboard Title:', d3.get('dashboard_title'))
print('Slug:', d3.get('slug'))
print('position_json structure:')
pos = json.loads(d3.get('position_json', '{}'))
print('GRID_ID children:', pos.get('GRID_ID', {}).get('children'))

for cid in [15, 16, 17, 18, 19, 20]:
    try:
        c_res = opener.open(f'http://localhost:8088/api/v1/chart/{cid}').read().decode('utf-8')
        c = json.loads(c_res)['result']
        print(f"\nChart {cid}: slice_name={c.get('slice_name')}, viz_type={c.get('viz_type')}")
        params = json.loads(c.get('params', '{}'))
        if cid in [15, 16]:
            print('  kpi_title:', params.get('kpi_title'))
            print('  kpi_subtitle:', params.get('kpi_subtitle'))
            print('  comparison_label:', params.get('comparison_label'))
        elif cid == 17:
            print('  metrics:', params.get('metrics'))
            print('  showVarianceDelta:', params.get('showVarianceDelta'))
            print('  full params:', json.dumps(params, indent=2))
        elif cid == 18:
            print('  metrics:', params.get('metrics'))
            print('  show_legend:', params.get('show_legend'))
            print('  full params:', json.dumps(params, indent=2))
        elif cid == 20:
            print('  full params:', json.dumps(params, indent=2))
    except Exception as e:
        print(f'Chart {cid} error:', e)
