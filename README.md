Secure & Cost‑Aware IaC Gate

FWI - researching section by section while doing the demos, every dependency is set apart from grafana 

Objective
The goal of this project is to build a secure and cost aware gating layer for the IaC pull requests. Each run of pull request will trigger a containerised GitHub Actions workflow → Checkov (which is used to get insight into misconfigurations) → Conftest/OPA (policy-as-code) → Terraform plan (change set) → Infracost (monthly cost delta). Their results will be stored as artefacts(JSON/JUnit/SARIF) which will be pushed as metrics/logs(Prometheus/Pushgateway or Loki) → Grafana dashboard (overview). This entire system is packaged with Docker → ensuring reproducible scans, and a Docker Compose demo stack which makes this solution easy to stand up, reset, and access. The dashboards will provide pass/fail status, violation trends, MTTR to fix, and cost movement per pull request. This will enable more informed merge decisions and continuous improvement.
Value
Less misconfigurations, easy to predict costs, clear evidence for audits and a repeatable workflow.
Ideas
Use an API key from BridgeCrew to provide inside of the severity of the Checkov checks for errors

Tech Stack
Checkov
Static analysis tool that is used for scanning IaC files/directories for misconfigurations and security issues. Follows the industry’s best practices using its built in policies while allowing custom rule definitions. It supports outputting scan results in various formats, which is useful for feedback and for feeding the data into dashboards. Allows me to catch and prevent insecure infrastructure in the early development process.

Infracost
An open-source tool used for estimating cloud costs before resources are deployed. It goes through the Terraform code and calculates the monthly cost change of the infrastructure. It outputs data in machine-readable forms such as JSON. Using that JSON output I will capture the cost delta for each run. The project can also set thresholds to alert or fail the pipeline if costs increase over a certain amount, at minimum, the cost info is surfaced in PR comments and forwarded to the dashboard for trend tracking.
