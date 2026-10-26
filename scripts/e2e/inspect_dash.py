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

req = urllib.request.Request('http://localhost:8088/api/v1/dashboard/3')
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))['result']
    print("Dashboard position_json:")
    print(json.dumps(json.loads(res['position_json']), indent=2))
