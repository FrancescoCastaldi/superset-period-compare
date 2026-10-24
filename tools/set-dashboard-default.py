#!/usr/bin/env python3
"""
Imposta il valore predefinito del filtro PeriodCompare della dashboard di prova, cosi'
la dashboard si apre gia' con riferimento e confronto applicati (utile per i test
automatici nel browser, senza cliccare sul filtro).

Uso (dentro il container di Superset):
    python set-dashboard-default.py --reference "2026-09-01 : 2026-10-01" \
        --comparison "2026-08-01 : 2026-09-01" --type values
    python set-dashboard-default.py --clear
"""

import argparse
import importlib.util
import json
import os


def load_setup_module():
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("setup_test_dashboard", os.path.join(here, "setup-test-dashboard.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8088")
    parser.add_argument("--user", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--reference")
    parser.add_argument("--comparison")
    parser.add_argument("--type", default="values", choices=["values", "difference", "percentage", "ratio"])
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    setup = load_setup_module()
    api = setup.Api(args.base, args.user, args.password)
    dash_id = setup.find_one(api, "dashboard", "slug", setup.DASHBOARD_SLUG)
    detail = api.call("GET", f"/api/v1/dashboard/{dash_id}")["result"]
    metadata = json.loads(detail["json_metadata"])
    flt = metadata["native_filter_configuration"][0]

    if args.clear or not args.reference:
        flt["defaultDataMask"] = {"extraFormData": {}, "filterState": {}, "ownState": {}}
    else:
        extra = {"time_range": args.reference}
        state = {"referenceRange": args.reference, "comparisonMode": "none", "customRange": None,
                 "comparisonType": args.type}
        if args.comparison:
            extra.update({"time_compare": [args.comparison], "comparison_type": args.type})
            state.update({"comparisonMode": "custom", "customRange": args.comparison})
        flt["defaultDataMask"] = {
            "extraFormData": extra,
            "filterState": {"value": state, "label": args.reference},
            "ownState": {},
        }
    api.call("PUT", f"/api/v1/dashboard/{dash_id}", {"json_metadata": json.dumps(metadata)})
    print(json.dumps(flt["defaultDataMask"]["extraFormData"]))


if __name__ == "__main__":
    main()
