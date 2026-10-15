# Delivery roadmap

The [build plan](../BUILD-PLAN.md) contains fifty implementation and thirty readiness
criteria. Existing local/deployed stages have separate focused acceptance records.
The single-business release has verified backend/frontend publication and bounded
owner-only Calendar/CRM/email evidence. Real native voice, complete operator UI
journeys, compatible-client MCP, provider deletion/backup replay and final
release closeout remain open in the
[single-business acceptance](pilot-completion-spec.md). A successful deployment
does not close those unrelated criteria.

The recorded owner-only Retell web call never joined browser media. Later provider
readback showed `error user not joined`, duration zero and cost zero; the owner
operation reached DONE and released its slot. Vapi has not been attempted and
the saved free-credit receipt is stale. The deployed exact-call recovery extension
adds provider-confirmed terminal reads for future delayed webhooks; its separate
[acceptance](native-reconciliation-spec.md) does not close real audio gates.
The next audio gates remain bounded Retell and Vapi tool checks with owner
listening, which the owner deferred on October 15. Publication and deployment dates
are recorded in the [October 15 recovery evidence](evidence/tenant-export-release-20261015.md), with the [October 13 owner release](evidence/owner-release-20261013.md) retained as history;
no completion due date has been agreed for the open voice and customer-readiness
gates. Future capacity dates depend on measured provider limits, workload and
funding decisions, so assigning a calendar deadline now would be unsupported.

| Workstream      | Foundation                                       | Next acceptance                                                       |
| --------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| Business engine | Persistent bookings, knowledge, jobs and tools   | Broader delivery receipts and ambiguous-delivery recovery             |
| Frontend        | Public/operator pages and HTTP console           | Authenticated live native-state journey, then more durable flows      |
| Native voice    | Retell/Vapi profiles/auth/lifecycle              | Intent/native bind/audio/tool/end-call flows on both platforms        |
| Custom voice    | ElevenLabs settings boundary                     | Rights, quality, pronunciation, latency and compatibility             |
| Identity        | Owner OIDC and revocable sessions                | Customer onboarding, MFA/recovery and role administration             |
| Legal/privacy   | Applicability register and local redaction       | Customer decisions, provider deletion, backup replay and contracts    |
| Capacity        | Guarded measurements                             | 1K -> 10K -> 100K -> 1M+ sessions; separate voice/mixed stages        |
| Reliability     | Immutable releases, parity, observer and restore | Redundancy, full 99%/99.9% SLO windows, off-device backup and RPO/RTO |
| Security        | Config/secret checks, scanners and access tests  | Penetration review, distributed limits and rotation drills            |
| Delivery        | Public source/docs and free CI                   | Versioned evidence, compatibility and reproducible handoff            |

Order: native/connector correctness -> customer identity/data lifecycle -> pagination/
limits/telemetry -> replicas -> database/worker failover -> staged capacity. High
voice concurrency requires provider/telephony capacity agreements.
The future capacity program treats one million registered accounts, one million
active dashboard sessions and one million simultaneous voice calls as separate
targets, with an additional mixed workload. The 99% baseline and 99.9% production
objective require defined indicators and full observation; neither is achieved.
Dates and instance counts cannot substitute for exit evidence. Each milestone
records release/workload/tests/review/dependencies. Chargeable tests need approval.
