import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
import sys

BASE_URL = "http://localhost:8088"
DASH_URL = f"{BASE_URL}/superset/dashboard/period-compare-test/"
LOGIN_URL = f"{BASE_URL}/login/"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Wait for server readiness
print(f"Connecting to Superset at {BASE_URL}...")
for attempt in range(1, 31):
    try:
        with opener.open(f"{BASE_URL}/health", timeout=5) as r:
            if r.getcode() == 200:
                print(f"Superset health check OK (attempt {attempt})")
                break
    except Exception as e:
        if attempt % 5 == 0 or attempt == 1:
            print(f"Waiting for server readiness... (attempt {attempt}/30): {e}")
        time.sleep(3)
else:
    print("Warning: Superset /health did not answer with 200 within timeout. Continuing anyway...")

# 2. Extract CSRF token from login page
csrf_token = ""
for attempt in range(1, 10):
    try:
        with opener.open(LOGIN_URL, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
            match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
            if match:
                csrf_token = match.group(1)
                print(f"Extracted CSRF token: {csrf_token[:10]}...")
                break
    except Exception as e:
        print(f"Login page fetch failed (attempt {attempt}/10): {e}")
        time.sleep(2)

# 3. Authenticate with admin credentials
form_data = urllib.parse.urlencode({
    "username": "admin",
    "password": "admin",
    "csrf_token": csrf_token,
}).encode("utf-8")

req = urllib.request.Request(LOGIN_URL, data=form_data)
try:
    with opener.open(req, timeout=10) as r:
        print(f"Login response HTTP {r.getcode()}")
except Exception as e:
    print(f"Login POST error: {e}")

# 4. Fetch dashboard page and parse bootstrap data
print(f"Fetching dashboard: {DASH_URL}")
try:
    with opener.open(DASH_URL, timeout=15) as r:
        dash_html = r.read().decode("utf-8", errors="ignore")
        print(f"Dashboard HTML received! Total length: {len(dash_html)} bytes")
        
        found_bootstrap = False
        for line in dash_html.splitlines():
            if "data-bootstrap" in line:
                found_bootstrap = True
                val_start = line.find('data-bootstrap="')
                if val_start != -1:
                    val = line[val_start + 16:]
                    val_end = val.find('"')
                    raw_json = val[:val_end].replace("&quot;", '"').replace("&#34;", '"')
                    data = json.loads(raw_json)
                    print(f"SUCCESS: Dashboard parsed successfully!")
                    print(f"data keys: {list(data.keys())}")
                    dash = data.get("dashboard_data") or data.get("dashboardData") or data
                    print(f"dash keys: {list(dash.keys()) if isinstance(dash, dict) else type(dash)}")
                    slices = dash.get("slices") or dash.get("charts") or []
                    print(f"Active charts count: {len(slices)}")
                    for s in slices:
                        slice_name = s.get("slice_name") or s.get("name")
                        viz_type = s.get("viz_type") or s.get("form_data", {}).get("viz_type")
                        print(f" - [{viz_type}] {slice_name}")
                    
                    # Native filters check
                    meta = dash.get("metadata") or {}
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            pass
                    native_filters = meta.get("native_filter_configuration", [])
                    print(f"Native filters configured: {len(native_filters)}")
                    for nf in native_filters:
                        print(f" - Filter: {nf.get('name')} (type: {nf.get('filterType')})")
                    break
        
        # 5. Also query the Dashboard REST API to inspect full slices and metadata
        api_dash_url = f"{BASE_URL}/api/v1/dashboard/period-compare-test"
        print(f"\nQuerying REST API: {api_dash_url}")
        with opener.open(api_dash_url, timeout=10) as api_r:
            api_data = json.loads(api_r.read().decode("utf-8")).get("result", {})
            print(f"API Dashboard Title: {api_data.get('dashboard_title')}")
            print(f"API Published: {api_data.get('published')}")
            api_slices = api_data.get("slices", [])
            print(f"API Active charts count: {len(api_slices)}")
            for s in api_slices:
                print(f" - [{s.get('viz_type')}] {s.get('slice_name')}")
            
            meta_str = api_data.get("json_metadata") or "{}"
            meta = json.loads(meta_str) if isinstance(meta_str, str) else meta_str
            native_filters = meta.get("native_filter_configuration", [])
            print(f"API Native filters configured: {len(native_filters)}")
            for nf in native_filters:
                print(f" - Filter: '{nf.get('name')}' (filterType: {nf.get('filterType')})")
                print(f"   Targets: {nf.get('targets')}")
                print(f"   Default value: {nf.get('defaultDataMask', {}).get('filterState')}")
except Exception as e:
    print(f"Error fetching dashboard: {e}")
    sys.exit(1)
