# Local core operation and recovery

The local development stage runs on loopback with test-data customers. Its
capability-based browser connection is for that stage only. The published pilot
uses Google owner login and secure server sessions. The operator and each business/management MCP read or write
scope check separate capabilities. Keep those five values in an ignored environment
file and the private credential recovery file. Never put them in browser URLs,
shell arguments, screenshots or public evidence.

The historical local engine meets eighteen test-data criteria. The authenticated
pilot is now published as backend03/frontend06 with144backend/78frontend tests,
12backend/6frontend file parity and current public21route/7HTTP checks. See
[pilot evidence](evidence/pilot-verification.md); actual voice and external delivery
remain separate unverified gates.
Vapi support identified the default Python header as the cause
of the earlier edge denial and authorized an application User-Agent/HTTPX request.
One read-only assistant inventory request returned HTTP 200. The configured owner
gate is resolved for this account; dedicated native profile configuration is verified, while calls/audio and external
business delivery remain untested/disabled.
Do not repeat the original rejected request or bypass any new security denial.

## Start from the existing checkout

Use Python 3.12–3.14 and Node 24 within the declared package engine range.
Install the pinned Python lock into an isolated environment and install the local
package without changing the lock. Install frontend dependencies with `npm ci`.
Populate all required settings from `.env.example` in an ignored environment file;
use separate randomly generated capabilities. The existing private setup already
contains configured values. Validate it without printing it.

From the project root:

```sh
python -m voicebridge.cli migrate --env-file .local/core-engine/.env
python -m voicebridge.cli seed --env-file .local/core-engine/.env
python -m voicebridge.cli api --env-file .local/core-engine/.env
```

In a separate process:

```sh
python -m voicebridge.cli worker --env-file .local/core-engine/.env
```

Use the configured virtual environment interpreter for these commands. The
worker must run independently of requests. Migrations are explicitly versioned;
do not replace them with `create_all`. Repeating migration/seed does not create a
second business. Commands currently require the checkout's migration configuration
and maintained data files; the wheel alone is not a complete deployment bundle.

Run `npm run dev`, open the displayed loopback address and route `#/engine`, then
enter the local operator capability. The capability stays in memory and reload
requires re-entry. Configure `VITE_CORE_API_URL` to the local API address and add
the exact frontend origin to `VB_ORIGINS`. A blank core URL disables connection.
`VITE_DEV_PORT` resolves collisions with the presentation server. On Windows-mounted
files under WSL, `VITE_DEV_POLLING=true` and a configured polling interval avoid
stale transforms; keep this setting local because polling adds work.

Health endpoints expose only liveness and local database/schema readiness.
They do not prove calendar/provider availability, worker activity or uptime.
State views return bounded record lists plus counts. Large datasets need paged
operator access before a large production workload is supported.

## Booking and jobs

Each booking operation needs a stable operation ID and explicit confirmation.
Retry the same request with the same ID after an uncertain response. Changed
inputs require a new ID; a conflict is a business result, not delivery failure.
Use a business-local ISO timestamp with the correct offset. Naive, invalid DST,
past, closed-hours, unsupported-service and overlapping reservations are rejected.

An accepted reservation is pending until the calendar receipt is verified.
Calendar jobs store immutable revisioned intent. Confirmed transitions atomically
enqueue CRM and follow-up work. A new revision supersedes obsolete calendar or
confirmation work. Follow-ups admit reserved `.invalid` recipients only in this
stage. Mailpit captures them locally and never relays to a real inbox.

Known failures have bounded retries and dead letters. Inspect job status, attempts,
detail and receipt before replaying. Replay admits only known failed/dead jobs.
Expired calendar leases are reconciled using the stable external ID; expired
delivery leases become `unknown`. Unknown CRM/email outcomes cannot be blindly
resent or marked successful. The current operator reconciliation action supports
calendar outcomes; unknown delivery needs a verified provider receipt and remains
unresolved until a receipt-based recovery path is available.

The authenticated local n8n workflow routes confirmations to Mailpit and returns
an SMTP message receipt and matching operation key. Its workflow template lives
in `infra/n8n/confirmation.workflow.json`; private credential IDs/values and the
installed workflow state belong in recovery records. Inspect the existing workflow
before importing/publishing. Do not recreate the owner or enable optional paid
assistants. SMTP acknowledgement proves local acceptance, not real customer delivery.

## Knowledge and evaluations

Text/Markdown and text-based PDF imports are validated before persistence. PDF
parsing runs in a disposable process with configured page, memory and time limits.
The API also limits concurrent parsers; excess PDF work returns HTTP 429 before
starting a parser. Limits apply per API process and must fit its resource budget;
Linux resource limits are required for this parser. Encrypted/scanned/malformed
documents are rejected. Revisions require the current revision; deletion removes
documents from active search. PostgreSQL search returns source identities and
revisions; absent, stale or explicitly conflicting facts abstain. Retrieved text
has data authority only and cannot authorize actions.

The nine versioned runtime cases cover approved/unsupported/adversarial questions,
explicit confirmation, timezone, tenant isolation, both provider envelopes,
successful booking through each adapter and an actually retrieved adversarial
document. test-data booking fixtures use isolated tenant records and a separate
local calendar namespace. Their workers claim only that fixture's tenant; the
business worker cannot execute fixture jobs against its own calendar.
Every accepted fixture booking receives persistent cancellation cleanup, including
pending or ambiguous results. Cleanup appears in the evaluation console; use
"Verify fixture cancellation" for unresolved fixtures. The authenticated endpoint
`POST /api/evaluations/{fixture_id}/cleanup` retries the owned fixture and verifies
its cancellation receipt. Existing business bookings are preserved.
Evaluation creates local call records with terminal events and makes no provider
API call. The automated suite additionally covers concurrent
booking, idempotency, lease loss, ambiguous writes, scope denial and revisions.
Acoustic quality, real call behavior and provider performance remain untested.

## Recovery after shutdown

Read the project checkpoint and dossier, then inspect Git, running processes and
the existing Docker project. Start stopped existing project containers; do not
recreate services, owners, calendars, keys or named volumes. Never run volume
deletion, global pruning or commands affecting other projects. The dependency
containers currently have restart policy `no`; Docker startup alone is insufficient.

After PostgreSQL is ready, migrate/seed if required, start the API and independent
worker, and inspect persisted booking/jobs before replay. Verify current credentials
privately. Existing named volumes and atomic checkpoints are not off-device backups
or proof of physical power-loss durability.

The owner's private, unpublished manual backup tool reads a consistent logical snapshot, restores it
into a newly named isolated database and compares every table's row count and hash:

```sh
python manual-tests/core_backup_restore_test.py \
  --env-file .local/core-engine/.env \
  --output .local/core-engine/backups/core-recovery.jsonl
```

It never replaces the working database and drops only its verified test clone.
These commands require the owner's separate tooling; they are not public-checkout
commands. Public backup/restore alternatives are in the section below.
Keep backups private: they can contain contact information and capability digests.
A verified administrative restore procedure and off-device encrypted retention
are required before a production release.

The automated process recovery checks run the actual CLI worker loop in isolated
fixture processes. They kill only those processes after a calendar write or SMTP
acceptance, let the real lease expire, then start a new worker. Configuration is
injected from the isolated fixture. Calendar recovery must keep one event;
uncertain SMTP delivery must remain unknown with no automatic second send:

```sh
python -m pytest tests/test_worker_process_recovery.py
```

The owner's private, unpublished workflow check uses the existing running API, independent
worker, authenticated n8n workflow and Mailpit. Supply the configured loopback
Mailpit URL. Its private intent file is flushed before booking so reruns use the
same operation rather than creating another reservation:

```sh
python manual-tests/core_n8n_journey_test.py \
  --env-file .local/core-engine/.env \
  --mailpit-url <configured-loopback-Mailpit-URL> \
  --intent .local/core-engine/journey-intent.json \
  --output .local/evidence/core-local-journey-latest.json
```

Inspect the intent and durable state before changing that file. Do not remove it
to retry an uncertain operation. The check verifies three completed jobs and one
captured message matching the follow-up receipt; it never releases captured mail.

## Public-checkout recovery alternatives

Install PostgreSQL client tools matching the database's supported major version.
Configure private `pg_service.conf`/password-file entries outside Git: one service
for the source and one for a separately created, empty, owned restore target.
Do not put database passwords or credential-bearing URLs in command arguments.
Create a private backup directory, then use standard PostgreSQL tools:

```sh
mkdir -p .local/backups
PGSERVICE=voicebridge-source pg_dump --format=custom --file=.local/backups/voicebridge.dump
pg_restore --list .local/backups/voicebridge.dump
# Only after verifying the restore service targets an empty isolated database:
PGSERVICE=voicebridge-restore pg_restore --dbname=voicebridge_restore \
  --no-owner --no-acl --exit-on-error --single-transaction .local/backups/voicebridge.dump
```

The target database must be created separately and its ownership checked before
the restore. Compare each table's counts and deterministic row hashes using a
private verification session, then test booking/knowledge/job/authentication flows.
The `pg_restore --list` check validates archive readability, not a successful restore.
Record restore duration and achieved RPO/RTO; never overwrite the working database
or publish backups. Standard tool syntax is documented by
[PostgreSQL backup guidance](https://www.postgresql.org/docs/current/backup-dump.html).

For ordinary checkout verification, use the committed HTTP/worker tests:

```sh
mkdir -p .local/core-engine .local/evidence
# Configure the isolated test environment described in docs/testing.md first.
python -m pytest tests/test_booking_engine.py tests/test_http_providers_knowledge.py
python -m pytest tests/test_worker_process_recovery.py
```

These exercise real HTTP and worker recovery without unpublished programs or
external provider calls. For a running local API, check configured loopback
`/health/live` and `/health/ready`, then the authorized console's persisted booking,
job and receipt state. Do not treat readiness alone as end-to-end delivery proof.

## Gates

Run backend pytest, strict Mypy, Ruff and the security scanners; frontend tests,
types, lint, formatting, build, packaging and release regressions; and
`npm run test:core-contracts`. Regenerate OpenAPI through the CLI and TypeScript
through `openapi-typescript` before reviewing drift. Run dependency audits and
the configuration/secret audit. Exercise real HTTP, separate-worker, MCP SDK,
browser and restore journeys, then obtain a fresh-context review.

Capacity evidence is bounded by `config/capacity-profiles.json`. It does not prove
one million users/calls or sustained uptime. Keep resource guards, no-cost limits
and provider execution gates intact. Google owner authentication and the bounded pilot release are verified. Real
voice rights/listening, external delivery, production onboarding, legal/compliance,
large-scale capacity and sustained uptime remain open.

## Existing deployed pilot recovery

Preserve the current server database, identity encryption key, accounts and native
profiles. Read the ignored recovery checkpoint and deployment evidence before any
action. First-creation helpers must never be replayed against the existing root.
Only a new frozen release may replace the owned API/worker/observer after drift
checks, snapshots, configuration equality, backup and rollback review. The explicit
preflight-resume path accepts only its known no-process-mutation journal stage and
independently rechecks all current artifacts; an unknown process outcome requires
inspection rather than a retry.

The latest33032-byte quiesced backup is valid PGDMP. The separately verified
restore used the earlier32787-byte backup and matched thirteen tables in an
isolated clone; do not claim the latest backup has also been restored. The working
database and capture mailbox stayed intact during the upgrade. API and worker
were quiesced, so zero downtime is not claimed.

Observation recorded101probes/100successes/one unsuccessful and zero unknown
seconds at the final check. That is a measured interval, not an achieved uptime
SLA. Preserve unsuccessful samples and the earlier release/review evidence.
