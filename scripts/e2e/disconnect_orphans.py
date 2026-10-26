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

for cid in [11, 12, 13, 14]:
    req = urllib.request.Request(f'http://localhost:8088/api/v1/chart/{cid}', data=json.dumps({"dashboards": []}).encode('utf-8'), method='PUT', headers=headers)
    with opener.open(req) as resp:
        print(f"Chart {cid} updated:", resp.getcode())

# Verify chart 11 dashboards
with opener.open(f'http://localhost:8088/api/v1/chart/11') as resp:
    res = json.loads(resp.read().decode('utf-8'))['result']
    print("Chart 11 dashboards now:", [d['id'] for d in res.get('dashboards', [])])
