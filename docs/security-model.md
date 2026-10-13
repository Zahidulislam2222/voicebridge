# Security model

Controls use [OWASP ASVS](https://owasp.org/projects/asvs) as a verification framework.
For a wider customer release, pin a specific ASVS version, map applicable Level 2
requirements to this threat model and attach test/review evidence. The present
table describes boundaries and open acceptance, not an ASVS certification.

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
| Transcript/privacy leakage    | Owner/tenant checks, ended-call redaction and late-event tombstone               | Provider deletion, backup replay and rights-request rehearsal    |
| Cost or quota exhaustion      | Disabled live voice, bounded native duration and guarded provider settings       | Distributed admission, account quotas and real-call limits       |

## Secrets and telemetry

Use ignored environment files or an approved secret store. Secrets never belong in
frontend settings, URLs, arguments, public logs or artifacts. Separate environments,
providers and scopes. Rotate affected values and revoke compromised sessions.

Log bounded error classes, operation/revision/outcome and correlation IDs. Redact
contacts, raw provider payloads, credentials and recordings. Avoid unbounded tenant/
call labels in metrics. Apply explicit audit access and retention.

The deployed single-business release keeps real voice and unrestricted external
mail disabled. A bounded owner-only Calendar/CRM/email receipt is evidence of that
specific path only. Before broader traffic, review vendor and caller permissions,
retention, provider artifact deletion, per-tenant limits and abuse alerts. The
[legal register](legal-and-privacy.md) owns jurisdiction-specific decisions.

## Supply chain and release

Pin dependencies/actions, verify registries and review locks. CI uses minimal
permissions, isolated test data, no production keys and no automatic deployment.
Keep hooks and push protection active; resolve findings without bypasses.
Deployment starts with drift detection, local changes/gates and a previous snapshot,
then compatible rollout/readiness and hash parity. Exercise post-activation rollback
and the actual served CSP. See [reporting](../SECURITY.md) and
[incident runbooks](operations-runbooks.md).

For each release, record exact artifact identity, dependency/advisory results,
secret and configuration audit, authorization-negative tests, scanner execution,
review verdict, live behavior and local/live parity in the
[release evidence](evidence/pilot-verification.md). A clean scan or passing build
cannot prove that external voice, customer data processing or future capacity is
safe without their own real-flow and independent assessment gates.
