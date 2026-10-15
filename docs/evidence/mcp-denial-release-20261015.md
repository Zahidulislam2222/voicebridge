# MCP denial audit release — 2026-10-15

Backend `20261015-mcp-denial-audit-18` is deployed with the unchanged frontend
`20261015-native-reconciliation-09`. All **16 backend files and 15 source modules**
match the reviewed local release. The deployment preserved 57 neighboring
containers and the gateway/frontend. The 35,707-byte PostgreSQL backup passed
format/digest checks; this backup was not independently restored.

Missing or wrong credentials, unavailable tools, read-only mutations,
foreign-tenant arguments, secret-read attempts and unapproved promotion are
denied and audited. Records contain fixed surface/capability/tool/reason labels;
credentials, request IDs, arguments and exception details are excluded. The typed
`VB_MCP_DENIAL_AUDIT_LIMIT_PER_MINUTE` default is 30 per bucket. Overflow adds one
marker and durable cumulative counts across minute rollover. Denial locks are
separate from booking locks. Audit-storage failures return sanitized 503 and
never permit denied tool execution. This is a row budget, not HTTP flood admission
control or a long-term retention policy.

## Verification

| Gate | Verified result |
| --- | --- |
| Scoped acceptance | A01–A06 met; independent implementation and exact release/guard approval |
| Backend | 234/234 tests passed in 171.86 seconds; 16 targeted MCP audit tests passed |
| Types/lint/build | Mypy 15 modules, configured runtime/tests Ruff, Python wheel/sdist and image build passed |
| Security/configuration | Bandit 0; Semgrep1.168.0 ran 79 rules on 15 modules with 0 findings/errors; source Gitleaks 0; 216 public files checked against 37 saved private values with 0 matches/private staging and complete environment coverage before documentation closeout |
| Deployment guards | 74/74 independently passed, including 20 archive identity regressions |
| Live HTTP | Seven denied cases produced seven fresh durable audit entries, read back through the protected management scope |
| Durable counts | Three appointments, three contacts, one historical call and ten jobs unchanged |
| Frontend | Unchanged frontend09 retains 97 tests, 21 packaged/21 actual routes and seven intercepted recovery journeys; these are the earlier recorded checks |

A fresh Chrome probe after packaging did not return and was terminated; this
release does not claim a fresh backend18 browser result. The unchanged frontend
and owner recovery16 had their own successful browser checks.

The first candidate17 archive was saved by image ID and omitted its release tag.
Its server preflight stopped after loading and before any process quiesce or
promotion. Candidate17 and its journal/archive remain preserved. Corrected18
uses the exact tagged save and a local pre-upload guard for Docker tag metadata,
OCI layout/annotations, descriptor/config identity and normalized duplicate
metadata paths. Negative regressions reproduce the missing-tag and format-selection
failures. [Docker save](https://docs.docker.com/reference/cli/docker/image/save/)
and the [containerd importer](https://github.com/containerd/containerd/blob/main/core/images/archive/importer.go)
explain the distinction between the saved identity and restored tag.

The mounted Semgrep scan completed successfully; a byte-identical Linux snapshot
also passed with the same rules and unchanged source hashes. An earlier empty
sandbox attempt was interrupted and retained. The two existing helper-only Ruff
S603 findings, frontend bundle-size warning and Docker ARG-default warning remain.
No scanner was suppressed and no dependency was added.

## Remaining work

The [MCP audit criteria](../mcp-denial-audit-spec.md) and original P9.4 are accepted
for the existing single-business static-capability endpoints. **25/50 implementation
and 0/30 readiness criteria** are accepted; 55 original requirements remain in the
[roadmap matrix](roadmap-status-20261015.md). This does not establish native assistant
client/OAuth compatibility, provider promotion, in-call MCP, full dashboard API
integration, exports/artifact isolation, real audio, provider deletion, legal
readiness, measured scale or sustained availability.

Voice creation and external email remain disabled; follow-ups are capture-only
with no recipients. No native call, external message, billing change, cloud
resource, Google Doc/PDF update or GitHub push occurred. Human voice listening is
deferred by the owner. [Earlier recovery16 evidence](reconciliation-release-20261015.md)
retains its dated scope.
