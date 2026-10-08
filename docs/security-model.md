# Security model

Controls use [OWASP ASVS](https://owasp.org/projects/asvs) as a verification framework.
Assess each against intended scope; scanners do not replace business-flow tests.

| Threat                        | Current boundary                                                                 | Additional acceptance                                            |
| ----------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Account/session theft         | OIDC validation, opaque encrypted server sessions, secure cookies and revocation | Customer MFA/recovery and abuse tests                            |
| Cross-tenant access           | Server identity binding and tenant-filtered services                             | Expanded role matrix, row policies and penetration review        |
| CSRF/privilege escalation     | CSRF and separate business/management scopes                                     | Every new route and administrative flow                          |
| Forged provider events        | Platform authentication then active-call capability                              | Real envelopes/audio, replay and quota tests                     |
| Prompt injection              | Retrieved text stays data; permission stays in code                              | Adversarial cases and handoff evaluation                         |
| Replayed side effects         | Locks, idempotency, revisions and receipts                                       | Cross-node contention and failure injection                      |
| Unknown delivery              | Explicit unknown state and receipt reconciliation                                | Non-calendar recovery expansion                                  |
| Documents/resource exhaustion | Isolated PDF parser and body/page/time/memory/concurrency limits                 | Global admission and multi-process tests                         |
| Secret/supply-chain exposure  | Lockfiles, private ignores, configuration tests and scanners                     | Advisory monitoring and rotation drills                          |
| Host compromise               | Non-root runtime, isolated services and readonly profiles                        | Central secrets, patching, least privilege and off-device backup |

## Secrets and telemetry

Use ignored environment files or an approved secret store. Secrets never belong in
frontend settings, URLs, arguments, public logs or artifacts. Separate environments,
providers and scopes. Rotate affected values and revoke compromised sessions.

Log bounded error classes, operation/revision/outcome and correlation IDs. Redact
contacts, raw provider payloads, credentials and recordings. Avoid unbounded tenant/
call labels in metrics. Apply explicit audit access and retention.

## Supply chain and release

Pin dependencies/actions, verify registries and review locks. CI uses minimal
permissions, isolated test data, no production keys and no automatic deployment.
Keep hooks and push protection active; resolve findings without bypasses.
Deployment starts with drift detection, local changes/gates and a previous snapshot,
then compatible rollout/readiness and hash parity. Exercise post-activation rollback
and the actual served CSP. See [reporting](../SECURITY.md) and
[incident runbooks](operations-runbooks.md).
