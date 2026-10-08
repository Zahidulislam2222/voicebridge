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
[PR #1](https://github.com/Zahidulislam2222/voicebridge/pull/1) passed all five
required checks before ordinary rebase merge. On the resulting main commit,
[quality](https://github.com/Zahidulislam2222/voicebridge/actions/runs/37708656892)
and [security](https://github.com/Zahidulislam2222/voicebridge/actions/runs/37708656800)
workflows both passed. All 194 remote file modes/hashes matched the local tree;
commit attribution remained the verified owner. See
[Actions](https://github.com/Zahidulislam2222/voicebridge/actions) for subsequent runs. No live deployment or real provider execution follows from CI.

The user authorized creation of the project overview after the accessible native
Google Docs inventory contained no matching project document. The new document and
its local PDF were then completed. Native readback verified the complete intended
text, forty headings, 103 list paragraphs, thirty-one native link runs and three date
chips, with no mismatches. The same document exported to a valid, non-empty PDF:
fifteen pages, 248,407 bytes. Every rendered page was inspected; privacy and boundary
checks found no issues. Canonical installation used a flushed temporary file and
verified hash before replacement; no previous project PDF existed.

Publication criteria PUB01–PUB12 are met for this scope, including the separately
authorized new-document route. Local gates and remote checks are recorded above;
actual HTTP/CLI worker recovery and native document/PDF export were exercised.
Independent reviews accepted publication preparation and the CI correction. The
broader product roadmap retains its own remaining acceptance gates.
The full business roadmap keeps its independent remaining acceptance gates.
