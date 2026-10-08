# VoiceBridge documentation

Implementation, development, integration, operation and the future scaling program
share this index. Current evidence and future acceptance gates have distinct scopes.

| Purpose                  | Documents                                                                                                                                                |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Product and architecture | [Root README](../README.md), [architecture](architecture.md)                                                                                             |
| Development              | [Frontend](../apps/web/README.md), [backend](../apps/api/README.md), [testing](testing.md), [contribution](../CONTRIBUTING.md)                           |
| Contracts/providers      | [API](api/README.md), [OpenAPI](api/core-openapi.json), [native interoperability](provider-interoperability-spec.md)                                     |
| Deployment               | [Frontend deployment](frontend-deployment.md), [engine operations](core-engine-operations.md), [templates](../deploy/README.md)                          |
| People and data          | [Legal/privacy](legal-and-privacy.md), [security](security-model.md), [reporting](../SECURITY.md), [rights](../THIRD-PARTY-NOTICES.md)                   |
| Capacity                 | [1M+ concurrency plan](capacity/scaling-roadmap.md), [bounded load criteria](capacity/core-load-spec.md)                                                 |
| Uptime/recovery          | [Reliability](reliability.md), [runbooks](operations-runbooks.md)                                                                                        |
| Delivery                 | [Roadmap](roadmap.md), [build plan](../BUILD-PLAN.md), [publication criteria](publication-spec.md)                                                       |
| Evidence                 | [Current deployment](evidence/pilot-verification.md), [local core](evidence/core-verification.md), [frontend history](evidence/frontend-verification.md) |

Historical evidence stays dated to its original scope. Later results supersede
only affected claims; one passing stage does not close unrelated gates.
