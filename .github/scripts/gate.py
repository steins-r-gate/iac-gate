#!/usr/bin/env python3
import argparse, json, os, sys
from collections import Counter

SEV_ORDER = ["CRITICAL","HIGH","MEDIUM","LOW","UNKNOWN"]

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def count_by_severity(checkov_json):
    failed = (checkov_json.get("results", {}) or {}).get("failed_checks", []) or []
    counts = Counter()
    for x in failed:
        # Checkov 3.x may use 'check_severity'; older outputs use 'severity'
        sev = (x.get("check_severity") or x.get("severity") or "UNKNOWN").upper()
        counts[sev] += 1
    total = sum(counts.values())
    return counts, total

def infracost_delta(ic_json):
    def to_float(s):
        try: return float(s)
        except Exception:
            try: return float(str(s).replace(",",""))
            except Exception: return 0.0
    if isinstance(ic_json, dict):
        if "summary" in ic_json and "diffTotalMonthlyCost" in ic_json["summary"]:
            return to_float(ic_json["summary"]["diffTotalMonthlyCost"])
        total = 0.0
        for p in ic_json.get("projects", []) or []:
            bd = p.get("breakdown") or {}
            if "diffTotalMonthlyCost" in bd:
                total += to_float(bd["diffTotalMonthlyCost"])
        return total
    return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkov", required=True)
    ap.add_argument("--infracost", required=True)
    ap.add_argument("--cost-warn", type=float, default=100.0)
    ap.add_argument("--cost-block", type=float, default=300.0)
    args = ap.parse_args()

    ck = load_json(args.checkov, {"results": {"failed_checks": []}})
    ic = load_json(args.infracost, {"summary": {"diffTotalMonthlyCost": "0"}})

    sev_counts, total_failed = count_by_severity(ck)
    high = sev_counts["HIGH"] + sev_counts["CRITICAL"]
    cost_diff = round(float(infracost_delta(ic)), 2)

    # Job summary
    lines = [
        "# IaC Gate Result",
        f"- Checkov failed checks: **{total_failed}** "
        + "( " + ", ".join(f"{s}: {sev_counts.get(s,0)}" for s in SEV_ORDER if sev_counts.get(s,0)) + " )",
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
