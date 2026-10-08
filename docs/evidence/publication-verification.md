# Publication verification

Publication scope: frontend/backend source, configuration, migrations, contracts,
build tools, READMEs and public engineering documentation. Runtime code is unchanged
by documentation publication. Date: 2026-10-08.

## Local evidence

| Gate                             | Result                                                                                                                       |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Frontend tests                   | 78 passed                                                                                                                    |
| Backend existing suite           | 144 passed in 132.33 seconds                                                                                                 |
| New security-tooling regressions | 4 passed                                                                                                                     |
| Types                            | TypeScript, Mypy14 runtime modules and Mypy1 scanner adapter passed                                                          |
| Lint/format                      | ESLint, Ruff application/tests, frontend/tooling formatting passed                                                           |
| Builds                           | Frontend/browser artifact and Python wheel/sdist passed                                                                      |
| Packaging/contracts              | 11 presentation/release/engine/OpenAPI checks passed                                                                         |
| Secret/configuration audit       | 190 public candidates compared with34 saved private values; no matches, no private staging and complete environment examples |
| Shared edit hook                 | Manual scan of190 public candidates passed                                                                                   |
| Installed pre-commit             | Gitleaks, Bandit and Semgrep all-files hooks passed                                                                          |
| Registry verification            | 87 pinned Python packages resolved from the real registry in a dry run                                                       |
| Independent review               | Follow-up review ready after six cold-start/documentation fixes; no remaining blockers                                       |

Backend tests use real isolated PostgreSQL and worker/OIDC/provider contract flows
with external sockets denied. New adapter tests cover native findings, Windows
positional arguments, invalid timeout and out-of-repository paths. The installed
hook remains active; scanner exit failures are not converted to success.

The frontend build retains its existing large-chunk warning. Application/test lint
and security scopes are declared above; a separate broad Ruff check of the scanner
adapter flags generic S603 subprocess-review warnings. They are unsuppressed; independent review found no shell-injection defect in the
configured invocation. Executable settings remain trusted repository configuration.

## Remote and document acceptance

Remote commit/tree/author, repository metadata/security settings and actual CI must
be verified after pushing. Google Doc/PDF acceptance follows successful publication.
The full business roadmap keeps its independent remaining acceptance gates.
