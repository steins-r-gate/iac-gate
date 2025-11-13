#!/usr/bin/env python3
import argparse, json, math, sys
from pathlib import Path

def _to_float(x):
    try:
        if isinstance(x, (int, float)): return float(x)
        if isinstance(x, str): return float(x.replace("$","").replace(",","").strip())
    except Exception:
        return None
    return None

def _deep_search_first(obj, keys):
    if isinstance(obj, dict):
        for k in keys:
            if k in obj:
                v = _to_float(obj[k])
                if v is not None:
                    return v
        for v in obj.values():
            found = _deep_search_first(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _deep_search_first(v, keys)
            if found is not None:
                return found
    return None

def _sum_projects_totals(js):
    total = 0.0
    projects = js.get("projects") if isinstance(js, dict) else None
    if not isinstance(projects, list):
        return None
    for p in projects:
        v = None
        for keys in (["summary","totalMonthlyCost"], ["breakdown","totalMonthlyCost"]):
            cur = p
            for k in keys:
                if isinstance(cur, dict) and k in cur:
                    cur = cur[k]
                else:
                    cur = None
                    break
            if cur is not None:
                v = _to_float(cur); break
        if v is None:
            v = _to_float(p.get("totalMonthlyCost"))
        if v is not None:
            total += v
    return total

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def total_from_breakdown(js):
    v = _deep_search_first(js, ["totalMonthlyCost"])
    if v is not None: return v
    v = _sum_projects_totals(js)
    return v if v is not None else 0.0

def delta_from_diff(js):
    return _deep_search_first(js, ["diffTotalMonthlyCost", "totalMonthlyCostDiff", "monthlyCostChange"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--pr", required=True)
    ap.add_argument("--diff", required=True)
    ap.add_argument("--abs-threshold", type=float, default=0.0)
    ap.add_argument("--pct-threshold", type=float, default=0.0)
    args = ap.parse_args()

    for p in (args.base, args.pr, args.diff):
        if not Path(p).is_file():
            print(f"Gate ERROR: missing file: {p}", file=sys.stderr); sys.exit(1)

    js_base = read_json(args.base)
    js_pr   = read_json(args.pr)
    js_diff = read_json(args.diff)

    delta = delta_from_diff(js_diff)
    base_total = total_from_breakdown(js_base)
    pr_total   = total_from_breakdown(js_pr)

    if delta is None:
        delta = pr_total - base_total

    delta = 0.0 if delta is None or math.isnan(delta) else float(delta)
    pct = (delta / base_total) if base_total and base_total > 0 else None

    reasons = []
    if args.abs_threshold and abs(delta) > args.abs_threshold:
        reasons.append(f"abs delta ${delta:,.2f} > ${args.abs_threshold:,.2f}")
    if pct is not None and args.pct_threshold and pct > args.pct_threshold:
        reasons.append(f"percent delta {pct*100:.2f}% > {args.pct_threshold*100:.2f}%")

    status_ok = (not reasons) or (delta <= 0)
    print("---- Infracost Gate ----")
    print(f"BASE total: ${base_total:,.2f}")
    print(f"PR   total: ${pr_total:,.2f}")
    print(f"Δ (PR-BASE): ${delta:,.2f}" + (f"  ({pct*100:.2f}%)" if pct is not None else ""))
    if status_ok:
        print("Gate PASSED: within thresholds (or change is a saving)."); sys.exit(0)
    else:
        print("Gate FAILED: " + "; ".join(reasons)); sys.exit(1)

if __name__ == "__main__":
    main()
