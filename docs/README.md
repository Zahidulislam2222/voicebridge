# VoiceBridge documentation

Implementation, development, integration, operation and the future scaling program
share this index. Current evidence and future acceptance gates have distinct scopes.

The authenticated single-business frontend and backend are deployed. Backend
release-file parity passed 16/16 checks and frontend parity passed 7/7; the
latest full backend suite exited successfully and 108 frontend tests passed.
The earlier unjoined Retell call ended. Creation is disabled; exact-call owner
recovery works independently of creation. Audio acceptance is open. Unrestricted
external mail remains disabled.
Read the [current release evidence](evidence/tenant-export-release-20261015.md) before treating any older count
or release note as current.

| Purpose                  | Documents                                                                                                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Product and architecture | [Root README](../README.md), [architecture](architecture.md), [configuration](configuration.md), [providers](integrations.md)                                                                                               |
| Development              | [Frontend](../apps/web/README.md), [backend](../apps/api/README.md), [testing](testing.md), [contribution](../CONTRIBUTING.md)                             |
| Contracts/providers      | [API](api/README.md), [OpenAPI](api/core-openapi.json), [native interoperability](provider-interoperability-spec.md)                                       |
| Deployment               | [Frontend deployment](frontend-deployment.md), [engine operations](core-engine-operations.md), [templates](../deploy/README.md)                            |
| People and data          | [Legal/privacy](legal-and-privacy.md), [security](security-model.md), [reporting](../SECURITY.md), [rights](../THIRD-PARTY-NOTICES.md)                     |
| Capacity                 | [1M+ concurrency plan](capacity/scaling-roadmap.md), [bounded load criteria](capacity/core-load-spec.md)                                                   |
| Uptime/recovery          | [Reliability](reliability.md), [monitoring](monitoring.md), [runbooks](operations-runbooks.md)                                                                                          |
| Delivery                 | [Roadmap](roadmap.md), [single-business acceptance](pilot-completion-spec.md), [build plan](../BUILD-PLAN.md), [publication criteria](publication-spec.md), [current publication](publication-20261015-spec.md) |
| Evidence                 | [Current deployment](evidence/tenant-export-release-20261015.md), [earlier release](evidence/pilot-verification.md), [local core](evidence/core-verification.md)     |

Historical evidence stays dated to its original scope. Later results supersede
only affected claims; one passing stage does not close unrelated gates.
