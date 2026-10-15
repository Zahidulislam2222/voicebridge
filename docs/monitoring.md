# Monitoring, alerting and operational ownership

Monitor user outcomes, not just process reachability. The current system has health
and schema-readiness endpoints, durable audit/job outcomes and bounded passive
observation evidence. The full monitoring/on-call program below is a delivery
workstream; continuous coverage and alert delivery need their own acceptance.

## Signals and accountable response

| Signal | Observation | Response / owner |
| --- | --- | --- |
| Website and authenticated API | Eligible route success, latency distribution, authorization failures and missing samples | Service maintainer triages user impact and release/dependency state |
| Booking integrity | Accepted intent to verified calendar receipt, conflicts, duplicates and unknown outcomes | Business-operations owner reconciles receipts; maintainer investigates consistency |
| Durable worker | Backlog age, lease age, retry/dead/unknown states and receipt delay | Operations owner applies bounded replay/reconciliation policy |
| Native voice | Admission/setup, media join, speech/tool latency, interruption/handoff and termination | Voice integration owner verifies provider/account quota and actual audio impact |
| Database/resources | Pool waits, query latency, locks, storage growth, CPU/memory and saturation | Infrastructure owner diagnoses bottlenecks before increasing admission |
| Security | Scope/tenant denials, webhook failures, session abuse, anomalous export volume and secret findings | Security owner contains scope and preserves private evidence |
| Providers/cost | Quota/rate-limit, timeout/error classes, approved spend envelope and disabled-execution drift | Integration owner stops unsafe admission and verifies account policy |
| Recovery | Backup age/integrity, restore rehearsal, RPO/RTO and rollback readiness | Data/release owner records actual recovery evidence |

Assign named people and escalation coverage before wider customer operation. For
this maintained repository, code/release ownership is recorded by the repository;
customer business/legal/communications ownership must be agreed per deployment.
A title in this table is not proof of staffed 24-hour coverage.

## Telemetry design

Record bounded event classes, request/operation correlation, release and outcome.
Exclude credentials, contact text, transcript/audio, raw provider payloads and
retrieved private content. Use bounded metric labels: avoid per-call IDs, contact
addresses or arbitrary tenant names as time-series dimensions. Protect traces and
audit queries with explicit role/tenant access and a retention schedule.

Separate time-based reachability, event-based availability and business correctness.
Declare denominators, deadlines and exclusions before measuring. Preserve unknown
telemetry intervals rather than treating missing data as success. Sampled traces
explain failures; durable receipts establish business outcomes.

## Alerts and verification

Use short/long burn-rate windows against the declared service objective, plus
backlog-age, storage/pool exhaustion, provider-quota and execution-policy alerts.
Thresholds belong in maintained operational configuration and must be exercised
against the measured workload. Alert severity depends on user impact and response
urgency; dashboards alone are not alert delivery.

Before launch, trigger each critical alert in an isolated environment, verify the
right recipient and escalation, acknowledge and resolve it, and record delay and
runbook effectiveness. Test monitoring failure and stale/no-data behavior. Every
alert needs an owner, threshold rationale, action/runbook, quieting policy and
retest date. Public reports summarize results without exposing telemetry endpoints
or private recipient details. See [reliability](reliability.md),
[runbooks](operations-runbooks.md) and [security](security-model.md).
