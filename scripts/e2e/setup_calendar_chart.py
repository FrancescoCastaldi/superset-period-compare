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

login_res = opener.open(urllib.request.Request(
    'http://localhost:8088/api/v1/security/login',
    data=json.dumps({"username": "admin", "password": "admin", "provider": "db", "refresh": True}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
))
token = json.loads(login_res.read().decode('utf-8'))['access_token']

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}",
    "X-CSRFToken": csrf,
    "Referer": "http://localhost:8088"
}

# Create or find Calendar Filter chart
q = json.dumps({"filters": [{"col": "viz_type", "opr": "eq", "value": "calendar_filter"}]})
res = opener.open(f'http://localhost:8088/api/v1/chart/?q={urllib.parse.quote(q)}').read().decode('utf-8')
existing = json.loads(res).get('result', [])

cal_params = {
    "datasource": "1__table",
    "viz_type": "calendar_filter",
    "groupby": ["order_date"],
    "date_column": "order_date",
    "metric": "sum_sales",
    "value_aggregation": "sum",
    "adhoc_filters": [],
    "color_scheme": "supersetColors",
    "scale_type": "linear",
    "show_legend": True,
    "first_day_of_week": 1,
    "locale": "it",
    "show_week_numbers": False,
    "show_year_dropdown": True,
    "enable_overview": True,
    "cell_density": "compact",
    "show_macro_shortcuts": True,
    "filter_type_mode": "auto",
    "in_value_format": "date",
    "default_value_mode": "none"
}

if existing:
    cal_id = existing[0]['id']
    req = urllib.request.Request(f'http://localhost:8088/api/v1/chart/{cal_id}', data=json.dumps({
        "slice_name": "Filtro Calendario (Calendar Filter)",
        "viz_type": "calendar_filter",
        "params": json.dumps(cal_params)
    }).encode('utf-8'), method='PUT', headers=headers)
    opener.open(req)
    print(f"Updated existing calendar chart {cal_id}")
else:
    req = urllib.request.Request('http://localhost:8088/api/v1/chart/', data=json.dumps({
        "slice_name": "Filtro Calendario (Calendar Filter)",
        "viz_type": "calendar_filter",
        "datasource_id": 1,
        "datasource_type": "table",
        "params": json.dumps(cal_params)
    }).encode('utf-8'), method='POST', headers=headers)
    with opener.open(req) as resp:
        cal_id = json.loads(resp.read().decode('utf-8'))['id']
    print(f"Created new calendar chart {cal_id}")

print("Calendar Chart ID:", cal_id)
