import subprocess
import json

out = subprocess.check_output(['docker', 'exec', 'superset_app', 'ls', '-1', '/app/superset/static/assets/']).decode('utf-8')
files = [f.strip() for f in out.splitlines() if f.strip().endswith('.js')]
print(f"Total JS files: {len(files)}")

for term in ['stratum_bar', 'hierarchical_table', 'stratum_heatmap', 'calendar_filter']:
    matched = []
    for i in range(0, len(files), 40):
        batch = files[i:i+40]
        res = subprocess.run(['docker', 'exec', 'superset_app', 'grep', '-l', term] + [f'/app/superset/static/assets/{f}' for f in batch], capture_output=True, text=True)
        if res.stdout:
            matched.extend([l.strip() for l in res.stdout.splitlines() if l.strip()])
    print(f"Matches for {term}: {matched}")
