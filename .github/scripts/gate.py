#!/usr/bin/env python3
import argparse, json, os, sys
from collections import Counter

SEV_ORDER = ["CRITICAL","HIGH","MEDIUM","LOW","UNKNOWN"]

def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _to_float(x):
    try:
        return float(x)
    except Exception:
        try:
            return float(str(x).replace(",", ""))
        except Exception:
            return 0.0

def checkov_counts(data):
    failed = (data.get("results", {}) or {}).get("failed_checks", []) or []
    counts = Counter()
    for x in failed:
        sev = (x.get("check_severity") or x.get("severity") or "UNKNOWN").upper()
        counts[sev] += 1
    total = sum(counts.values())
    return counts, total

def infracost_total(data):
    return _to_float((data.get("summary") or {}).get("totalMonthlyCost", 0))

def infracost_delta_from_diff(diff_json):
    s = diff_json.get("summary") or {}
    if "diffTotalMonthlyCost" in s:
        return _to_float(s["diffTotalMonthlyCost"])
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkov", required=True)
    ap.add_argument("--infracost", required=True, help="PR breakdown JSON")
    ap.add_argument("--infracost-base", help="BASE breakdown JSON")
    ap.add_argument("--cost-warn", type=float, default=100.0)
    ap.add_argument("--cost-block", type=float, default=300.0)
    args = ap.parse_args()

    ck = _load(args.checkov, {"results": {"failed_checks": []}})
    ic_pr = _load(args.infracost, {"summary": {"totalMonthlyCost": "0"}})

    # Prefer computing delta ourselves from two breakdowns if base is supplied
    cost_diff = None
    if args.infracost_base:
        ic_base = _load(args.infracost_base, {"summary": {"totalMonthlyCost": "0"}})
        cost_diff = infracost_total(ic_pr) - infracost_total(ic_base)

    # If no base given, or totals fail, try diff JSON if the caller passed it instead
    if cost_diff is None:
        cost_diff = infracost_delta_from_diff(ic_pr)
    if cost_diff is None:
        cost_diff = 0.0

    cost_diff = round(float(cost_diff), 2)

    sev_counts, total_failed = checkov_counts(ck)
    high = sev_counts["HIGH"] + sev_counts["CRITICAL"]

    # Job summary
    lines = [
        "# IaC Gate Result",
        f"- Checkov failed checks: **{total_failed}** ( " + ", ".join(
            f"{s}: {sev_counts.get(s,0)}" for s in SEV_ORDER if sev_counts.get(s,0)) + " )",
        f"- Infracost monthly cost delta: **€{cost_diff:.2f}**",
        f"- Thresholds: warn ≥ €{args.cost_warn}, block ≥ €{args.cost_block}",
    ]
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    # Gate decision
    reasons, exit_code = [], 0
    if high > 0:
        reasons.append(f"{high} HIGH/CRITICAL security findings")
        exit_code = 1
    if cost_diff >= args.cost_block:
        reasons.append(f"cost increase €{cost_diff:.2f} ≥ block (€{args.cost_block})")
        exit_code = 1

    if exit_code:
        print("❌ Gate FAILED:", "; ".join(reasons))
    else:
        note = f" — ⚠ cost warning (≥ €{args.cost_warn})" if cost_diff >= args.cost_warn else ""
        print(f"✅ Gate PASSED (Checkov HIGH/CRITICAL=0; cost Δ=€{cost_diff:.2f}){note}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
