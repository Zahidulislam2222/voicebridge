# GitHub automation

`quality.yml` runs frontend and backend gates on standard Linux runners with an
isolated PostgreSQL service. `security.yml` adapts the installed security template
for Gitleaks, Bandit and Semgrep. Workflow actions are pinned to reviewed commits.

Permissions are read-only. There are no production secrets, provider calls, public
artifact uploads or deployments. Paid AI review stays disabled. Contributors use
pull requests; sensitive reports use private vulnerability reporting.
