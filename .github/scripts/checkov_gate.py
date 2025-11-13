#!/usr/bin/env python3
"""
Gate on Checkov JSON results.

Fail if CRITICAL/HIGH exceed thresholds (defaults: any CRITICAL/HIGH fail).
Example:
  python checkov_gate.py --json results/checkov.json --max-critical 0 --max-high 0 --max-medium 5
"""
import argparse, json, sys
from pathlib import Path
from collections import Counter

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="Path to Checkov JSON output")
    ap.add_argument("--max-critical", type=int, default=0)
    ap.add_argument("--max-high", type=int, default=0)
    ap.add_argument("--max-medium", type=int, default=999999)
    ap.add_argument("--max-low", type=int, default=999999)
    args = ap.parse_args()

    path = Path(args.json)
    if not path.is_file():
        print(f"Gate ERROR: missing Checkov JSON: {path}", file=sys.stderr)
        sys.exit(1)

    data = load_json(path)

    # Checkov JSON has .results.failed_checks (list of dicts with 'severity')
    failed = []
    results = data.get("results") or {}
    failed_checks = results.get("failed_checks") or []
    for fc in failed_checks:
        sev = (fc.get("severity") or "").upper()
        if not sev:
            sev = (fc.get("check_severity") or "").upper()
        failed.append(sev)

    counts = Counter(failed)
    crit = counts.get("CRITICAL", 0)
    high = counts.get("HIGH", 0)
    med  = counts.get("MEDIUM", 0)
    low  = counts.get("LOW", 0)

    print("---- Checkov Gate ----")
    print(f"CRITICAL: {crit}  HIGH: {high}  MEDIUM: {med}  LOW: {low}")
    reasons = []
    if crit > args.max_critical:
        reasons.append(f"CRITICAL {crit} > {args.max_critical}")
    if high > args.max_high:
        reasons.append(f"HIGH {high} > {args.max_high}")
    if med > args.max_medium:
        reasons.append(f"MEDIUM {med} > {args.max_medium}")
    if low > args.max_low:
        reasons.append(f"LOW {low} > {args.max_low}")

    if reasons:
        print("Gate FAILED: " + "; ".join(reasons))
        sys.exit(1)
    else:
        print("Gate PASSED: within severity thresholds.")
        sys.exit(0)

if __name__ == "__main__":
    main()
