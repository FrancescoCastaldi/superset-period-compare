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

res = opener.open('http://localhost:8088/api/v1/dataset/1').read().decode('utf-8')
dataset = json.loads(res)['result']
print("Columns:")
for c in dataset.get('columns', []):
    print(" -", c['column_name'], c['type'])

print("\nMetrics:")
for m in dataset.get('metrics', []):
    print(" -", m['metric_name'], ":", m['expression'])
