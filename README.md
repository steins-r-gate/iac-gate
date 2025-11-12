Secure & Cost-Aware IaC Gate (MVP)

A lightweight, PR-time “policy gate” for Terraform that blocks risky and expensive changes before they’re merged. The gate runs in GitHub Actions, scans your IaC for misconfigurations (Checkov) and estimates monthly cost deltas (Infracost). Results are uploaded as artifacts and summarised in the job output. No cloud credentials or terraform apply are required for the demo.

✅ Current MVP: Checkov + Infracost + gating script
🧭 Roadmap (optional later): Terraform plan (JSON) + OPA/Conftest, containerised toolchain, and Grafana/Loki/Prometheus dashboards.

How it works

Trigger: pull_request (opened/sync/reopened)
Steps:

Checkout repo

Run Checkov on infra/ → outputs results/checkov.json

Run Infracost on infra/ → outputs results/infracost.json

If the secret INFRACOST_API_KEY is missing (e.g., forked PR), we write a fallback JSON with cost = 0 so the job never crashes.

gate.py applies simple rules:

Fail if any HIGH/CRITICAL Checkov findings

Fail if cost delta ≥ €300 (warn at €100–299)

Upload results/ as a build artifact

Expected first-run behaviour: The sample Terraform deliberately lacks S3 encryption and exposes public reads; Checkov should flag HIGH/CRITICAL findings. The EC2 instance type provides a visible cost delta for Infracost.

Repository layout
.
├─ infra/
│  └─ main.tf                  # demo resources (intentionally misconfigured)
├─ .github/
│  └─ workflows/
│     └─ iac-gate.yml          # GitHub Actions pipeline
└─ .github/scripts/
   └─ gate.py                  # gating logic (security + cost thresholds)

Quick start (5–10 minutes)

Create secret (for real cost numbers)
Repo → Settings → Secrets and variables → Actions → New repository secret

Name: INFRACOST_API_KEY

Value: your API key (free account at Infracost)

Use the provided files

.github/workflows/iac-gate.yml (PR workflow)

.github/scripts/gate.py (gate logic)

infra/main.tf (intentionally risky + costy demo)

Open a PR from a branch in the same repo
Secrets are available to same-repo PRs. Forked PRs will see cost=0 (fallback) but still run the gate.

Read the output

Job summary shows total Checkov fails, HIGH/CRITICAL count, and cost delta (€).

Artifacts: results/checkov.json and results/infracost.json.

Configuration

Thresholds: edit in the workflow step that runs gate.py

--cost-warn 100 --cost-block 300


Currency: set INFRACOST_CURRENCY env var (default in workflow is EUR).

Terraform region: infra/main.tf sets provider "aws" { region = "eu-west-1" } purely for static analysis; we never apply.

Security & secrets

Do not commit API keys.

INFRACOST_API_KEY is read from GitHub Actions → Secrets.

For forked PRs, the workflow writes a fallback JSON (diffTotalMonthlyCost = 0) so the pipeline remains stable without secrets.

Roadmap (later, not needed for the MVP demo)

Terraform plan (JSON) + OPA/Conftest rules for policy-as-code on the change set

Docker/Compose to pin tool versions and make the stack reproducible

Observability: push gate outcomes/metrics to Prometheus/Pushgateway or logs to Loki → Grafana dashboard (pass/fail trend, MTTR, cost movement)

Troubleshooting

Infracost shows €0

Secret missing or PR from a fork → expected fallback. For real numbers, create the secret and open PR from a branch in the same repo.

No Checkov output

Ensure the path is infra/ and there’s at least one .tf file.

Gate doesn’t fail on security

You may have “fixed” the insecure bits; add a known HIGH/CRITICAL issue or lower the blocking threshold.


