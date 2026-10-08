# Delivery roadmap

The [build plan](../BUILD-PLAN.md) contains fifty implementation and thirty readiness
criteria. Existing local/deployed stages have separate focused acceptance records.

| Workstream      | Foundation                                       | Next acceptance                                                |
| --------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| Business engine | Persistent bookings, knowledge, jobs and tools   | Production receipts and ambiguous-delivery recovery            |
| Frontend        | Public/operator pages and HTTP console           | Route splitting, paging and more persistent operator flows     |
| Native voice    | Retell/Vapi profiles/auth/lifecycle              | Intent/native bind/audio/tool/end-call flows on both platforms |
| Custom voice    | ElevenLabs settings boundary                     | Rights, quality, pronunciation, latency and compatibility      |
| Identity        | Owner OIDC and revocable sessions                | Customer onboarding, MFA/recovery and role administration      |
| Legal/privacy   | Applicability register                           | Customer decisions, retention/deletion and contracts           |
| Capacity        | Guarded measurements                             | 1K -> 10K -> 100K -> 1M+ sessions; separate voice/mixed stages |
| Reliability     | Immutable releases, parity, observer and restore | Redundancy, full SLO window, off-device backup and RPO/RTO     |
| Security        | Config/secret checks, scanners and access tests  | Penetration review, distributed limits and rotation drills     |
| Delivery        | Public source/docs and free CI                   | Versioned evidence, compatibility and reproducible handoff     |

Order: native/connector correctness -> customer identity/data lifecycle -> pagination/
limits/telemetry -> replicas -> database/worker failover -> staged capacity. High
voice concurrency requires provider/telephony capacity agreements.
Dates and instance counts cannot substitute for exit evidence. Each milestone
records release/workload/tests/review/dependencies. Chargeable tests need approval.
