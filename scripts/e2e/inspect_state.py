import http.cookiejar
import json
import re
import urllib.parse
import urllib.request

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_html = opener.open('http://localhost:8088/login/').read().decode('utf-8')
csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_html).group(1)
data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin', 'csrf_token': csrf}).encode('utf-8')
opener.open('http://localhost:8088/login/', data=data)

# Dashboard 3
res = opener.open('http://localhost:8088/api/v1/dashboard/3').read().decode('utf-8')
dash = json.loads(res)['result']
print("Dashboard 3 Title:", dash.get('dashboard_title'))
print("Dashboard 3 Slug:", dash.get('slug'))
print("Dashboard 3 Slices in API:", [s['id'] for s in dash.get('slices', [])])
print("Dashboard 3 metadata:", dash.get('json_metadata'))

# All charts
q = urllib.parse.quote(json.dumps({'page_size': 100}))
charts_res = opener.open(f'http://localhost:8088/api/v1/chart/?q={q}').read().decode('utf-8')
charts = json.loads(charts_res)['result']
print("\nAll Charts in Superset:")
for c in charts:
    d_ids = [d['id'] for d in c.get('dashboards', [])]
    print(f"Chart ID: {c['id']}, Name: {c['slice_name']}, viz_type: {c['viz_type']}, Dashboards: {d_ids}")
