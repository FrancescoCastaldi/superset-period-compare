import http.cookiejar
import json
import re
import urllib.parse
import urllib.request

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

with opener.open('http://localhost:8088/login/') as r:
    html = r.read().decode('utf-8', errors='ignore')
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    csrf_token = match.group(1) if match else ''

form_data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin', 'csrf_token': csrf_token}).encode()
req = urllib.request.Request('http://localhost:8088/login/', data=form_data)
with opener.open(req) as r:
    pass

with opener.open('http://localhost:8088/superset/dashboard/period-compare-test/') as r:
    dash_html = r.read().decode('utf-8', errors='ignore')
    print('Dashboard page fetched! Total length:', len(dash_html))
    for line in dash_html.splitlines():
        if 'data-bootstrap' in line:
            print('Found data-bootstrap! length:', len(line))
            # extract json
            val_start = line.find('data-bootstrap="')
            if val_start != -1:
                val = line[val_start + 16:]
                val_end = val.find('"')
                raw_json = val[:val_end].replace('&quot;', '"').replace('&#34;', '"')
                data = json.loads(raw_json)
                print('Top-level bootstrap data keys:', list(data.keys()))
                dash = data.get('dashboard_data') or data.get('dashboardData') or data
                print('Dashboard keys:', list(dash.keys()) if isinstance(dash, dict) else type(dash))
                if isinstance(dash, dict):
                    print('Dashboard Title:', dash.get('dashboard_title') or dash.get('title'))
                    slices = dash.get('slices') or dash.get('charts') or []
                    print('Slices count:', len(slices))
                    for s in slices:
                        print(' - Slice:', s)
