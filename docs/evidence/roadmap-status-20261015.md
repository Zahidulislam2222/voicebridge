# Roadmap acceptance — 2026-10-15

An independent per-criterion review reconciled all 80 original requirements with
existing implementation and dated verification. **26/50 implementation criteria
are accepted for their stated scope; 0/30 readiness criteria are complete.**
The other 54 rows retain their original requirements. These counts are not a
product-completion percentage. Historical journeys were reviewed as evidence,
not all replayed in this audit; the current release has separate fresh gates.

Evidence anchors: B [build plan](../../BUILD-PLAN.md); F [frontend verification](frontend-verification.md);
C [core verification](core-verification.md); A [authenticated release](pilot-verification.md);
I [provider contracts](../provider-interoperability-spec.md); G [publication](publication-verification.md);
N [release completion](../pilot-completion-spec.md); R [legal](../legal-and-privacy.md),
[security](../security-model.md), [reliability](../reliability.md) and
[scaling](../capacity/scaling-roadmap.md). Current release behavior is recorded in
[current export release](tenant-export-release-20261015.md) and [earlier recovery release](reconciliation-release-20261015.md).

The twelve presentation/operator destinations remain controlled local experiences;
`#/engine` is the authenticated persistent console. Actual Retell/Vapi audio,
human listening, native assistant-client MCP, provider/backup deletion, legal
launch review, million-scale workloads and sustained service objectives remain
unaccepted. The owner deferred listening; deployment cannot close those gates.

## Implementation criteria

| ID | Status | Evidence and exact remaining boundary |
| --- | --- | --- |
| P1.1 | Accepted | B/F/C product contracts define configured repair business, owner/operator/viewer/unauthenticated boundaries, isolated verification data, end-to-end flow and exclusions. Guest access is denied rather than invented as a customer account feature. |
| P1.2 | Accepted | publication and release evidence record actual Git, ignored/unstaged/history-safe private files and installed Gitleaks/Bandit/Semgrep hook execution. Automatic edit-hook dispatch on every edit remains unproven; this criterion specifically requires demonstrated configured scanner/installed-hook execution, which exists. |
| P1.3 | Accepted | G records exact runtimes, registry verification, locked dependency setup, successful clean CI installation and applicable tests/types/lint/build commands. This accepts the reproducible foundation; the broader production-readiness gate is assessed separately under P10.1. |
| P1.4 | Accepted | C01/C02/C03/C08–C13, typed contracts/settings, generated OpenAPI/client drift tests and documented configuration inventory establish schemas, state transitions and configuration owners for the implemented system. |
| P1.5 | Accepted | Initial owned PostgreSQL/n8n/Mailpit setup and controlled adapters were started/verified; G clean CI creates isolated PostgreSQL/Mailpit and installs from locks. tests/conftest.py explicitly rejects non-loopback sockets and real-enabled provider/delivery settings. |
| P2.1 | Accepted | F records all eight public/twelve operator destinations at 375/768/1024/1440 widths, 32 public + 52 operator layouts, navigation/focus and corrected overflow findings. Later packaged route checks preserve scope; this is presentation acceptance. |
| P2.2 | Accepted | F operator browser journeys and workspace-service tests demonstrate agent/voice coherence and controlled linked call/booking/contact/job creation. No actual voice is implied. |
| P2.3 | Accepted | F explicitly exercises empty/search, input/error/permission, viewer restrictions, destructive confirmations and loading/retry UI states. |
| P2.4 | Accepted | F records keyboard skip/focus/dialog return, form validation and principal journey in real browser plus component/type/build gates. |
| P2.5 | Partial | No real sends/private credentials in controlled flow is evidenced, but original B requires every controlled screen/test state clearly labelled. Later owner-amended W09 deliberately changed visible labels; F notes that amendment. Do not silently check unchanged original wording. Resolve/record a precise accepted presentation-scope amendment, or reintroduce relevant-action local-state disclosure. |
| P3.1 | Partial | C/A prove real #/engine HTTP/PostgreSQL actions, restart persistence and generated contract consistency. docs/frontend-deployment.md explicitly states twelve other operator destinations remain local verification experiences. Whole original 'Dashboard actions use real API' is not substantiated for the entire planned operator application. |
| P3.2 | Accepted | A R01–R03/R07 plus tests/test_oidc_sessions.py prove real HTTP OIDC/session expiry/roles/CSRF/origin/tamper/replay; actual Google owner browser login/logout and copied-cookie revocation are recorded. Every adversarial case need not be repeated acoustically. |
| P3.3 | Accepted | E01–E08: two actual local OIDC tenants exercise record/job/export/local-artifact isolation, forged selectors, owner/session/CSRF and role denials, ended/tombstone/race/late-event protection; safe bounded projected exports pass252 backend tests,108 frontend tests, nine download/cancellation journeys, frozen review and live19/10 parity. Actual owner exports200 with two durable audits and unchanged business counts. Provider recording access and broader privacy evidence remain separate. |
| P3.4 | Accepted | tests/test_auth_migration.py upgrades/downgrades populated core without payload changes; clean fixtures apply migrations. release evidence record isolated current business-stage backup with 13-table before/restore/after counts and hashes. Later deployment backups still need their own restore; do not claim all backups validated. |
| P3.5 | Accepted | HTTP malformed/oversized/non-echo tests, bounded document import, typed hide-input errors, secret/private exclusion audits and complete environment example coverage substantiate current API/frontend boundary. Past diagnostic test-DSN disclosures were incident-recorded/rotated, not erased from history or recast as application response success. |
| P4.1 | Accepted | release/completion evidence F06, data/core/voice-design.json and private saved voice/design/save-plan/journal prove one original AI-generated ElevenLabs male voice, verified owner account, creation method/generation settings and attribution/owner-only noncommercial rights boundary. This row requires documented creation/rights/settings, not commercial portability; commercial use and actual Retell/Vapi reuse remain separate unaccepted gates. |
| P4.2 | External gate | No Retell joined audio, custom-voice browser/approved phone-path result or representative authorized call recordings. No-join registration is not this evidence. |
| P4.3 | Accepted | C08/C09/I P01–P05 and tests/test_http_providers_knowledge.py/test_provider_transcripts.py prove authenticated HTTP signatures/bearer, deduplication, ordering and exact server-owned call/tenant binding denials. Accepted adapter-contract scope, not live provider-originated acoustic evidence. |
| P4.4 | External gate | Human listening/interruptions/names/noise/silence/handoff and observed speech latency deferred by owner. |
| P4.5 | Partial | Native owner/CSRF, one-call lease, stale-entitlement and 60-second configured provider limits are tested/read back. Real duration enforcement/destination/phone-path and bounded call behavior still need native acceptance; account balance observations are dated, not permanent permission. |
| P5.1 | External gate | Real authenticated owner web booking has Calendar/DB/UI readback; no real voice caller checks/confirmation/booking exists. |
| P5.2 | Accepted | C04, tests/test_booking_engine.py concurrent overlapping reservations/stable payload and both-provider tool tests show one application-controlled confirmed reservation under concurrent/repeated requests. Does not promise uniqueness against arbitrary out-of-band calendar edits. |
| P5.3 | Partial | C05 and calendar timeout/rejection/reconciliation tests prevent false confirmed API/tool outcomes. 'No false spoken confirmation' remains unobserved without actual call/tool speech. |
| P5.4 | Accepted | C03/C05 plus booking DST/timezone/hours, cancellation/rescheduling/revision tests, unauthorized call-bound lookup/change denial and recorded direct Calendar lifecycle cover the business-service behavior. No claim of verified spoken corrections. |
| P5.5 | Partial | A/N F04 and direct CRM matching readback verified; CRM receipt/ambiguous match/failure code tests exist. Explicit revoked OAuth + missing-scope CRM recovery/visibility journeys were not found. An ordinary 200 receipt does not prove those cases. |
| P6.1 | Accepted | C06/C16 record real local HTTP -> worker -> authenticated n8n -> Mailpit with one matching captured confirmation and completed jobs; source includes transactional durable outbox and versioned workflow. No production n8n claim. |
| P6.2 | Partial | C07 and tests/test_worker_process_recovery.py exercise actual worker process death/lease expiry/no resend; no corresponding n8n death/restart accepted-job drill was found. |
| P6.3 | Accepted | C04/C07/C09, lease fencing/replay/idempotence tests and duplicate/reordered provider event tests prevent repeats of supported idempotent operations; ambiguous non-idempotent delivery stays unknown. |
| P6.4 | Partial | Worker retry/dead/unknown state and API reconcile/replay are implemented; controlled dashboard retry and historical core browser evidence exist. Whole actual persistent operator recovery UI journey with audited safe replay/ambiguous receipt handling is not specifically recorded and F08 remains open. |
| P6.5 | Accepted | A/release/completion evidence F05 record exactly one explicitly approved owner Gmail confirmation, provider/job receipt and actual inbox readback; restart/cancel caused no duplicate send. Local n8n editor is authenticated/private. Accept only this bounded recipient test; external delivery remains disabled now. |
| P7.1 | Accepted | C11, tests/test_document_import.py and knowledge HTTP tests exercise text/Markdown/PDF, revisions/search/delete, malformed MIME/text/PDF and capacity failures preserving usable prior knowledge. |
| P7.2 | Accepted | C11 and knowledge/review regression tests verify exact source IDs/revisions, stale/absent/contradictory abstention including conflicts outside matched query passages. |
| P7.3 | Accepted | C10/C11, test_document_instructions_have_no_action_authority, tenant isolation and retrieved-adversarial evaluation prove documents cannot grant actions/secrets through implemented deterministic service. No general LLM jailbreak guarantee. |
| P7.4 | External gate | Maintained nine-case deterministic evaluation suite exists with tool outcomes, but no real call transcripts/listening notes/acoustic results. |
| P7.5 | Partial | Versioned critical deterministic cases exist; no release-linked prompt/model/knowledge baseline comparison and declared quality-target evaluation report was found. A passing current suite is not a baseline comparison. |
| P8.1 | External gate | Actual Vapi custom ElevenLabs voice/browser/phone-path unverified; no Vapi native create/audio attempted. |
| P8.2 | External gate | Both adapters share controlled business tools, but neither has completed the full actual voice booking/CRM/follow-up journey. |
| P8.3 | Accepted | I/C08/C09 plus Vapi-specific HTTP event/tool payload, capability/bearer, tenant, malformed batch, duplicate/out-of-order and transcript lifecycle regressions substantiate adapter tests. Not proof that a native call emitted those envelopes. |
| P8.4 | External gate | Comparable listening/latency/outcome/cost evidence missing for both providers. Retell no-join zero-cost record is not a comparison sample. |
| P8.5 | Accepted | C09/C12 provider parity and parameterized shared-booking tests use selected profiles/adapters with unchanged business service, both provider contracts remain tested. Accepted code/controlled parity scope only. |
| P9.1 | External gate | Official MCP SDK four-scope HTTPS discovery/invocation is verified; actual compatible assistant-client use is explicitly untested. SDK is not evidence of native Claude/ChatGPT model-context behavior. |
| P9.2 | External gate | Scoped draft edits/revisions exist, but management promote_agent always denies pending separate approval; no actual assistant-client draft -> approved verified provider promotion walkthrough. |
| P9.3 | External gate | Retell/Vapi use HTTP custom-tool adapter paths; real-call MCP transport/tools not exercised. Sharing business functions does not establish MCP in-call use. |
| P9.4 | Accepted | A01–A06, 16 isolated MCP denial tests, 234 full backend tests, independent review and seven actual HTTP denials with seven durable audit readbacks prove missing scopes/foreign tenant arguments/secret reads/unapproved promotion fail without business changes. Fixed vocabulary, per-bucket row limits, cumulative overflow and sanitized storage failure are verified; this accepts the existing static-capability endpoints, not native-client/OAuth or provider promotion. |
| P9.5 | External gate | Native supported Claude walkthrough and separately requested ChatGPT surface missing; unsupported remains incomplete. |
| P10.1 | Partial | Current export19/10 passed252 backend and108 frontend checks,13 release/contracts, scoped static/security/build gates, exact review and16/7file parity.74 archive/deployment guards have prior independent evidence. Full readiness remains open, including the two existing helper-only whole-repository Ruff findings and the broader matrix. |
| P10.2 | Partial | Guarded local 40-request/4-client tests and passive health samples show their bounded result; complete declared workload outage/rate/spend-visible behavior evidence absent. No production/million-call inference. |
| P10.3 | External gate | Isolated restore, real rollback and credential rotations have evidence; provider retention/deletion, deletion-after-restore and OAuth revocation drills remain incomplete. |
| P10.4 | Partial | Current backend19/frontend10 are on the existing host with16/7 local/live file parity,15 source modules, owned-only promotion, readiness and retained rollback;21 actual routes and two owner exports passed. Broader release readiness, real audio and the original full system gate remain open. |
| P10.5 | External gate | Sanitized guides and actual defect/fix narratives exist. Authorized working voice recordings, all original 50 criteria and final full-release acceptance do not. |


## Readiness criteria

No readiness criterion is proposed closed from planning documents alone.

| ID | Status | Evidence and exact remaining boundary |
| --- | --- | --- |
| L1 | External gate | Legal register is applicability questions/guidance, not a reviewed named-owner actual jurisdiction/use-case/data-flow matrix for launch. |
| L2 | External gate | Configured AI/recording notice and permission checks exist; real disclosure/consent/refusal/outbound suppression journeys absent. |
| L3 | External gate | Free/noncommercial voice restrictions and n8n setup recorded; enabled-scope vendor DPA/subprocessors/transfers/access locations/usage-right verification incomplete. |
| L4 | External gate | Local transcript tombstone exists; full rights/withdrawal/provider deletion/backup recovery and qualifying-breach rehearsal absent. |
| L5 | External gate | No qualified legal launch assessment recorded. Agent-authored register is not legal signoff. |
| S1 | Partial | config/capacity-profiles.json defines target numbers and bounded local limits; mixed_workload is literally not-yet-measured. No complete region/tenant distributions/upstream/backend calculated demand profile. |
| S2 | Partial | DB pools, server sessions, tenant locks, durable workers and basic limits exist; multi-replica/worker-scaling/shared-stage tests not exercised. |
| S3 | Partial | Small populated-query/restore timing exists; stage caching/growth thresholds and migration/partition/shard consistency/privacy recovery evidence absent. |
| S4 | External gate | Dated small free account balances/inventory are not account-specific capacity/arrival/region/contract/budget commitments for claimed scale. |
| S5 | External gate | Bounded baseline does not provide sustained/burst/skew/mixed/failure benchmarks or upstream-supported million-call evidence. |
| R1 | Partial | docs/reliability.md names indicators/rolling thirty-day objectives; validated complete per-indicator eligibility/latency/degraded/error-budget policy config and reviewed owners absent. |
| R2 | External gate | Current single shared host is an explicit failure domain; no approved redundant topology/failover demonstration. |
| R3 | Partial | Isolated backup count/hash restoration exists; scoped measured RTO/RPO, off-host integrity, deletion-after-restore and disaster-recovery exercise incomplete. |
| R4 | Partial | Actual bad-release rollback/worker recovery exists; dependency/zone drills, on-call escalation and exercised error-budget release decisions absent. |
| R5 | External gate | No complete valid 99.9% indicator observation window at declared load; passive sampler explicitly never claims sustained uptime. |
| H1 | Partial | Security-model boundary table exists; pinned ASVS requirement/evidence map, full reviewed threat model and accountable owners remain future work. |
| H2 | Partial | Real admin two-step verification, OIDC/CSRF/revocation and adapter tests pass; complete privileged reauthentication/MFA/recovery and endpoint/job/artifact adversarial matrix not evidenced. |
| H3 | Partial | API-only secret separation, narrow DB, build exclusions and rotations proved; full retained-data/backups encryption/key lifecycle and verified protected local recovery filesystem/disk access controls not evidenced. |
| H4 | Partial | Tenant/injection/upload/replay/body/rate checks exist; admitted-load comprehensive abuse/SSRF/distributed quota exercise and denied-action traceability incomplete, MCP denial auditing is now verified, while broader HTTP/auth denial traceability and abuse coverage remain incomplete. |
| H5 | Partial | Actual hook/CI scanners, advisory audit and scoped reviews pass historically; container/SBOM checks, independent comprehensive security assessment, patch/incident-response exercise incomplete. |
| M1 | Partial | Business audit/state and passive readiness exist; implemented HTTP middleware has no correlated request logs/metrics/traces propagated across HTTP/tool/job/provider flows. No universal privacy-safe correlation evidence. |
| M2 | Partial | User usage/job counters and passive health are implemented; versioned complete indicator/voice/provider quota/spend/DB queue saturation dashboards absent. |
| M3 | External gate | No actual primary/backup service/security/quota/error-budget alert delivery, acknowledgement or escalation evidence. |
| M4 | Partial | Worker process death/unknown receipt and rollback drills exist; outage/latency/retry-storm/collector death/missing-telemetry detection and recovery not comprehensively exercised. |
| M5 | Partial | Protected bounded audit/sanitized response checks exist; retention/sampling/cardinality/cost/peak-load/monitoring-failure reliability verification incomplete. |
| D1 | Partial | Docs list roles and general triggers; named accountable legal/security/capacity/operations/API/release owners and launch acceptance missing. |
| D2 | Partial | Generated OpenAPI/settings examples drift checks exist. Generated API contracts are current; complete cross-document release and integration consistency remains a broader gate. Whole release-matching documentation criterion incomplete. |
| D3 | Partial | Docs link existing scoped tests and future gates honestly; legal/security/capacity/reliability/monitoring requirements-to-results/applicability maps are not complete. |
| D4 | Partial | Agent-executed clean CI/setup/restore/rollback evidence exists. No authorized operator uses full guides to recreate, respond to actual alert, restore and recover without undocumented steps. Missing alert system blocks this row too. |
| D5 | Partial | Historical scrubbed release reports/reviews/dossier updates exist; all implemented and future release requirements still need complete owner/evidence mappings and change-trigger coverage. Google Doc/PDF is explicitly locked without current update request. |
