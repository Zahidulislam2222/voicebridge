# Publication verification

Publication scope: frontend/backend source, configuration, migrations, contracts,
build tools, READMEs and public engineering documentation. Runtime code is unchanged
by documentation publication. Date: 2026-10-08.

## Local evidence

| Gate                       | Result                                                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Frontend tests             | 78 passed                                                                                                                    |
| Backend and tooling suite  | 150 passed in 108.84 seconds                                                                                                 |
| Focused CI recovery checks | 4 passed                                                                                                                     |
| Types                      | TypeScript, Mypy14 runtime modules and Mypy1 scanner adapter passed                                                          |
| Lint/format                | ESLint, Ruff application/tests, frontend/tooling formatting passed                                                           |
| Builds                     | Frontend/browser artifact and Python wheel/sdist passed                                                                      |
| Packaging/contracts        | 11 presentation/release/engine/OpenAPI checks passed                                                                         |
| Secret/configuration audit | 193 public candidates compared with34 saved private values; no matches, no private staging and complete environment examples |
| Shared edit hook           | Manual scan of190 public candidates passed                                                                                   |
| Installed pre-commit       | Gitleaks, Bandit and Semgrep all-files hooks passed                                                                          |
| Registry verification      | 87 pinned Python packages resolved from the real registry in a dry run                                                       |
| Independent review         | Follow-up review ready after six cold-start/documentation fixes; no remaining blockers                                       |

Backend tests use real isolated PostgreSQL and worker/OIDC/provider contract flows
with external sockets denied. New adapter tests cover native findings, Windows
positional arguments, invalid timeout and out-of-repository paths. The installed
hook remains active; scanner exit failures are not converted to success.

The frontend build retains its existing large-chunk warning. Application/test lint
and security scopes are declared above; a separate broad Ruff check of the scanner
adapter flags generic S603 subprocess-review warnings. They are unsuppressed; independent review found no shell-injection defect in the
configured invocation. Executable settings remain trusted repository configuration.

## Remote and document acceptance

The public repository is [Zahidulislam2222/voicebridge](https://github.com/Zahidulislam2222/voicebridge).
The initial commit author was verified as Zahidul Islam, attributed to that account.
All 193 initial published file modes and hashes matched the local commit. Private
files were absent. Secret scanning, push protection, private vulnerability reporting,
vulnerability alerts and five required CI checks are enabled.

The first security workflow passed all three scanners. The first quality workflow
passed frontend checks and exposed a missing capture-SMTP dependency in backend CI:
147 tests passed and the follow-up worker process-recovery test failed. The corrective
workflow declares digest-pinned Mailpit, with SMTP only and no relay configuration.
The complete corrected local suite passes 150 tests, including two CI environment
regressions; an independent read-only review accepted the correction.
See [Actions](https://github.com/Zahidulislam2222/voicebridge/actions) for final remote
run results. No live deployment or real provider execution follows from CI.

The user authorized creation of the project overview after the accessible native
Google Docs inventory contained no matching project document. The new document and
its validated local PDF remain separate deliverables.
The full business roadmap keeps its independent remaining acceptance gates.
