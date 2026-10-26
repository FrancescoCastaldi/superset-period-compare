import urllib.request, urllib.parse, http.cookiejar, json, re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
html = opener.open('http://localhost:8088/login/').read().decode('utf-8')
csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin', 'csrf_token': csrf}).encode('utf-8')
opener.open('http://localhost:8088/login/', data=data)

headers = {'Content-Type': 'application/json', 'X-CSRFToken': csrf}

# Let's inspect OpenAPI schema for PUT /api/v1/dashboard/{id}
try:
    req = urllib.request.Request(
        'http://localhost:8088/api/v1/dashboard/3',
        data=json.dumps({'slices': [15, 16, 17, 18, 19, 20]}).encode('utf-8'),
        headers=headers,
        method='PUT'
    )
    with opener.open(req) as r:
        print("Success:", r.status)
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode('utf-8'))
