import os
import subprocess
import time
import sys

PLUGINS_BASE = r'D:\Actual\03_Sviluppo_Software\Repositories\superset-plugins'

PLUGINS = [
    {
        'name': 'superset-plugin-chart-kpi-comparison',
        'test_cmd': ['node', 'node_modules/jest/bin/jest.js'],
        'build_cmd': ['node', 'scripts/build.mjs'],
        'out_bundle': 'dist/index.esm.js',
    },
    {
        'name': 'superset-plugin-chart-hierarchical-table',
        'test_cmd': ['node', 'node_modules/jest/bin/jest.js'],
        'build_cmd': ['node', 'scripts/build.mjs'],
        'out_bundle': 'dist/index.esm.js',
    },
    {
        'name': 'superset-plugin-chart-stratum-bar',
        'test_cmd': ['node', 'node_modules/jest/bin/jest.js'],
        'build_cmd': ['node', 'scripts/build.mjs'],
        'out_bundle': 'dist/index.esm.js',
    },
    {
        'name': 'superset-plugin-chart-stratum-heatmap',
        'test_cmd': ['node', 'node_modules/vitest/vitest.mjs', 'run', '--root', '.'],
        'build_cmd': ['node', 'scripts/build.mjs'],
        'out_bundle': 'dist/index.esm.js',
    },
    {
        'name': 'superset-plugin-chart-calendar-filter',
        'test_cmd': ['node', 'node_modules/jest/bin/jest.js'],
        'build_cmd': ['node', 'scripts/build.mjs'],
        'out_bundle': 'dist/index.esm.js',
    },
]

print("=== CONSOLIDATED 5-PLUGIN BUILD & TEST SUITE ===")
total_tests_passed = 0
results = []

for p in PLUGINS:
    p_dir = os.path.join(PLUGINS_BASE, p['name'])
    print(f"\n---> Testing & Building {p['name']}...")
    
    # 1. Run tests
    t0 = time.time()
    test_res = subprocess.run(p['test_cmd'], cwd=p_dir, capture_output=True, text=True)
    dt_test = time.time() - t0
    
    test_ok = test_res.returncode == 0
    test_output = test_res.stdout + test_res.stderr
    
    # Extract test counts if possible
    passed_count = "?"
    for line in test_output.splitlines():
        if "Tests:" in line and "passed" in line:
            passed_count = line.strip()
        elif "Tests" in line and "passed" in line:
            passed_count = line.strip()
            
    print(f"     Test result: {'OK' if test_ok else 'FAIL'} ({passed_count}) in {dt_test:.1f}s")
    if not test_ok:
        print("     Error output snippet:\n", test_output[-500:])
        
    # 2. Run build
    t0 = time.time()
    build_res = subprocess.run(p['build_cmd'], cwd=p_dir, capture_output=True, text=True)
    dt_build = time.time() - t0
    build_ok = build_res.returncode == 0
    
    bundle_path = os.path.join(p_dir, p['out_bundle'])
    bundle_size = os.path.getsize(bundle_path) if os.path.exists(bundle_path) else 0
    print(f"     Build result: {'OK' if build_ok else 'FAIL'} (Bundle size: {bundle_size/1024:.1f} KB) in {dt_build:.1f}s")
    
    results.append({
        'name': p['name'],
        'test_ok': test_ok,
        'build_ok': build_ok,
        'summary': passed_count,
        'bundle_kb': bundle_size / 1024,
    })

print("\n" + "="*60)
print("SUMMARY TABLE:")
print(f"{'Plugin Name':<42} | {'Tests':<18} | {'Build':<6} | {'Bundle':<9}")
print("-" * 80)
all_ok = True
for r in results:
    status = "OK" if r['test_ok'] else "FAIL"
    build_status = "OK" if r['build_ok'] else "FAIL"
    print(f"{r['name']:<42} | {status:<5} ({r['summary']}) | {build_status:<6} | {r['bundle_kb']:>6.1f} KB")
    if not r['test_ok'] or not r['build_ok']:
        all_ok = False

print("="*60)
if all_ok:
    print("ALL 5 PROPRIETARY PLUGINS PASSED 100% UNIT TESTS AND BUILT CLEANLY!")
else:
    print("WARNING: Some plugins failed.")
