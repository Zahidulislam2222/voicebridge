# VoiceBridge documentation

Implementation, development, integration, operation and the future scaling program
share this index. Current evidence and future acceptance gates have distinct scopes.

The authenticated single-business frontend and backend are deployed. Backend
release 20 passed 16/16 file and 15/15 source-module parity, frontend release 10
passed 7/7, the full 254-test backend suite passed and 108 frontend tests passed.
The owner voice route allows a bounded three-minute Retell call once a current
free-credit receipt (at most two hours old) is released; the deployed receipt is
expired, so calls are refused before any provider request. Exact-call owner recovery
works independently of creation. Real audio acceptance is open. Unrestricted
external mail remains disabled.
Read the [current release evidence](evidence/voice-release-20261025.md) before treating any older count
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
| Evidence                 | [Current deployment](evidence/voice-release-20261025.md), [October 15 release](evidence/tenant-export-release-20261015.md), [earlier release](evidence/pilot-verification.md), [local core](evidence/core-verification.md) |

Historical evidence stays dated to its original scope. Later results supersede
only affected claims; one passing stage does not close unrelated gates.
