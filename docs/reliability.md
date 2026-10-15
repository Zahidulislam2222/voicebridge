# Reliability, uptime objectives and recovery

Future baseline: **99%**. Production objective: **99.9%** for declared service
indicators. Neither has been demonstrated by the current single-server release.
The build plan retains its stronger production gate. An SLA requires a separate
contract, eligibility and remedies. Recorded observation scope is in
[deployment evidence](evidence/tenant-export-release-20261015.md).

| Indicator | Good event                                            | Measurement                                                  |
| --------- | ----------------------------------------------------- | ------------------------------------------------------------ |
| API       | Eligible request meets its result/latency threshold   | Valid authorized requests; client errors recorded separately |
| Booking   | Valid intent reaches calendar receipt before deadline | Accepted eligible intents; business conflict is distinct     |
| Worker    | Eligible job reaches receipt before deadline          | Admitted jobs; unknown outcome is not success                |
| Voice     | Admitted call meets setup/audio/tool requirements     | Calls within approved quota; setup/audio/tools separated     |
| Website   | Required routes remain usable within budget           | Actual requests plus declared external probe cadence         |

Use rolling thirty-day and shorter burn-rate windows. Record workload/release,
sample count, errors, latency histograms and unknown telemetry intervals. Keep
time-based reachability separate from event-based availability. Health endpoints
prove only their declared scope, not usable voice/external delivery. Missing samples
are never silently successful.

In a thirty-day time-based window, 99% permits 432 minutes, 99.5% permits 216 minutes,
and 99.9% permits 43.2 minutes of unavailability. Event budgets instead use
`eligible events × (1 − objective)`. Measurement policy follows
[Google's SLO guidance](https://sre.google/workbook/implementing-slos/).

## Error budgets and redundancy

Define eligibility, thresholds, exclusions and queries before observing. Version
them as operational configuration. Alert on fast/slow burn; exhausted budgets
prioritize repair over risky releases. Exclusions remain visible; maintenance counts
unless the declared contract explicitly says otherwise.

The current server is a host failure domain. Future releases add redundant API,
independent workers, database failover and regional recovery with booking uniqueness,
tenant and receipt-integrity drills. Provider failure needs bounded admission and
human handoff; mid-call provider switching has its own native-flow contract.

The latest deployment passed release-file parity and point-in-time readiness;
those checks establish neither a full observation window nor tolerance of this
host's failure. A 99% or 99.9% achieved claim requires the declared eligible
traffic, complete 30-day telemetry, error classification and measured results for
each named indicator. Voice remains outside an achieved indicator until real calls
and their setup, audio and tool results are observed.

Use readiness-driven rolling/canary release, compatible schemas, graceful draining
and lease reconciliation. Expand/migrate/contract schema changes preserve rollback
where possible. Test application/configuration/data compatibility. Zero-downtime
rollout is an exercised goal, not a guarantee against every failure.

## Disaster recovery

Planning objectives: RPO at most fifteen minutes and RTO at most sixty minutes for
the defined failure class. Validate before contractual use. Evaluate WAL/PITR,
encryption, independent storage, key recovery and regional placement; logical
snapshots alone do not meet every recovery objective.

Restore data/configuration/migration state into an isolated target, compare counts/
hashes and exercise business flows. Record achieved RPO/RTO, duration and cleanup.
An earlier backup's restore does not validate a later backup. Test unavailable
primary storage and expired credentials. Agent checkpoints are recovery notes,
not off-device backups or physical power-loss proof.

## Monitoring and drills

Measure latency/errors, locks/pools, worker lag/leases/unknown outcomes, provider
quotas, session errors and resources. Redact private data. Assign primary/backup
incident owners and alerts. Drill node loss, worker crash after side effect,
database failover, bad release, provider denial, telemetry loss and restore.

## Service-specific observation and release policy

Measure website usability, authorized API responses, booking receipts, worker
completion and native voice setup/audio/tools separately. A health endpoint can
remain green while an external calendar or media provider is unavailable. Define
each indicator's eligible events, deadline, threshold, observation source, no-data
policy and owner. Protect business correctness during overload rather than count
incorrect or duplicated bookings as successful availability.

Publish the exact observation window, release/workload, numerator/denominator,
latency distribution, missing intervals and incidents. The99% baseline and 99.9%
production objective use explicit error-budget policies; contract SLA terms need
their own approved scope/remedies. A short deployment check cannot establish a
rolling 30-day result. Follow [Google SLO practice](https://sre.google/workbook/implementing-slos/)
for indicator definition and error-budget decisions.

When burn rate threatens the budget, prioritize user-impact mitigation, hold risky
changes, inspect the relevant dependency and apply a verified rollback or admission
limit. Resume normal release pace only under the agreed budget policy. Monitoring
and alert delivery must also be exercised when a dependency or telemetry source
fails. See [operational monitoring](monitoring.md).

## Backup, availability and recovery evidence

Availability and recoverability are distinct. Verify backup freshness, integrity,
encryption/key recovery, off-device location and permission boundaries; restore
into an isolated environment and compare schema, row/content hashes and business
flows. Reapply lawful deletion/tombstone policy before admitting restored traffic.
Measure actual RPO/RTO against customer-approved targets and record failed drills.
A format-checked backup or a recovery checkpoint is not a successful restore.

The current host is one failure domain. Redundancy, database/worker failover,
regional recovery and sustained provider performance remain staged architecture
and acceptance work. Define dependencies and thresholds before changing topology;
retain immutable compatible artifacts and separately verified data recovery.
