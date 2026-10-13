# VoiceBridge documentation

Implementation, development, integration, operation and the future scaling program
share this index. Current evidence and future acceptance gates have distinct scopes.

The authenticated single-business frontend and backend are deployed. Backend
release-file parity passed 16/16 checks and frontend parity passed 7/7; the
latest full backend suite exited successfully and 97 frontend tests passed.
One owner-only Retell web call was registered without media; its occupied slot
needs reconciliation before another call. Audio acceptance is open. Unrestricted
external mail remains disabled.
Read the [current release evidence](evidence/owner-release-20261013.md) before treating any older count
or release note as current.

| Purpose                  | Documents                                                                                                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Product and architecture | [Root README](../README.md), [architecture](architecture.md)                                                                                               |
| Development              | [Frontend](../apps/web/README.md), [backend](../apps/api/README.md), [testing](testing.md), [contribution](../CONTRIBUTING.md)                             |
| Contracts/providers      | [API](api/README.md), [OpenAPI](api/core-openapi.json), [native interoperability](provider-interoperability-spec.md)                                       |
| Deployment               | [Frontend deployment](frontend-deployment.md), [engine operations](core-engine-operations.md), [templates](../deploy/README.md)                            |
| People and data          | [Legal/privacy](legal-and-privacy.md), [security](security-model.md), [reporting](../SECURITY.md), [rights](../THIRD-PARTY-NOTICES.md)                     |
| Capacity                 | [1M+ concurrency plan](capacity/scaling-roadmap.md), [bounded load criteria](capacity/core-load-spec.md)                                                   |
| Uptime/recovery          | [Reliability](reliability.md), [runbooks](operations-runbooks.md)                                                                                          |
| Delivery                 | [Roadmap](roadmap.md), [single-business acceptance](pilot-completion-spec.md), [build plan](../BUILD-PLAN.md), [publication criteria](publication-spec.md) |
| Evidence                 | [Current deployment](evidence/owner-release-20261013.md), [earlier pilot](evidence/pilot-verification.md), [local core](evidence/core-verification.md)     |

Historical evidence stays dated to its original scope. Later results supersede
only affected claims; one passing stage does not close unrelated gates.
