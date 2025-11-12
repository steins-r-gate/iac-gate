#!/usr/bin/env python3
import argparse, json, os, sys

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def count_high_from_checkov(data):
    failed = (data.get("results", {}) or {}).get("failed_checks", []) or []
    high = sum(1 for x in failed if str(x.get("severity","")).upper() in {"HIGH","CRITICAL"})
    return high, len(failed)

def infracost_delta(data):
    def to_float(s):
        try:
            return float(s)
        except Exception:
            try:
                return float(str(s).replace(",",""))
            except Exception:
                return 0.0
    if isinstance(data, dict):
        if "summary" in data and "diffTotalMonthlyCost" in data["summary"]:
            return to_float(data["summary"]["diffTotalMonthlyCost"])
        total = 0.0
        for p in data.get("projects", []) or []:
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

    high, total_failed = count_high_from_checkov(ck)
    cost_diff = round(float(infracost_delta(ic)), 2)

    # PR summary
    summary_lines = [
        "# IaC Gate Result",
        f"- Checkov failed checks: **{total_failed}** (HIGH/CRITICAL: **{high}**)",
        f"- Infracost monthly cost delta: **€{cost_diff:.2f}**",
        f"- Thresholds: warn ≥ €{args.cost_warn}, block ≥ €{args.cost_block}",
    ]
    gsum = os.environ.get("GITHUB_STEP_SUMMARY")
    if gsum:
        with open(gsum, "a", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")

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
        print(f"✅ Gate PASSED (Checkov HIGH=0; cost Δ=€{cost_diff:.2f}){note}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
