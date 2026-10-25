# VoiceBridge backend

FastAPI/Pydantic define HTTP contracts; SQLAlchemy/PostgreSQL persist business
records; Alembic maintains schema history. An independent durable worker executes
calendar, CRM and follow-up jobs. Retell, Vapi and scoped MCP use the same services.

## Setup

Use Python 3.12–3.14. Create/activate an isolated Python environment at the repository
root, install `requirements.lock`, then install the project without re-resolving:

```sh
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
```

Populate a private environment file from `.env.example`; configure PostgreSQL,
unique capabilities and business data. Examples are test credentials only.
Keep `VB_PROVIDER__ENABLED=false` and follow-up capture enabled locally. The
deployed single-business release has an owner-only native route with isolated
API credentials. Creation is enabled for the owner but each call requires a
current free-credit receipt (`VB_NATIVE_ENTITLEMENT_TTL_SECONDS`, at most 7200)
and an exact provider-profile match; `VB_NATIVE_MAX_SECONDS` caps calls at no more
than 180 seconds. The deployed receipt is expired, so creation fails closed before
any provider request. Separately gated GET-only recovery can verify and retire an
exact bound call. Native audio and Vapi acceptance remain open. Unrestricted email
delivery remains disabled. An earlier owner-only Calendar/CRM/email receipt
verifies a bounded path; it does not authorize general delivery.

```sh
python -m voicebridge.cli migrate --env-file .env.local
python -m voicebridge.cli seed --env-file .env.local
python -m voicebridge.cli api --env-file .env.local
# Separate process:
python -m voicebridge.cli worker --env-file .env.local
```

The wheel requires the checkout's data and migration configuration; deployment
bundles include them. Never replace migrations with automatic table creation or
recreate an existing database to apply a code change.

## Authentication and consistency

Local capabilities and deployed OIDC sessions are separate access modes. Server
identity binding owns tenant/role. Mutations require authorization, explicit
confirmation where appropriate, stable operation IDs and expected revisions.
Provider credentials establish platform identity; bounded call capabilities
establish active-call scope. Ended calls cannot regain tool authority. The
owner-only transcript redaction action requires an ended, same-tenant call and
creates a local tombstone against late provider events; provider-held artifacts
and historical backups require separate deletion/recovery verification.

Workers persist leases, attempts and receipts. Known failures back off; ambiguous
non-idempotent delivery stays unknown until receipt reconciliation. Knowledge text
never grants tool permission. PDF parsing has configured resource/concurrency limits.

## Verification

The suite requires loopback PostgreSQL with permission to create/drop generated
test databases. Configure its private `.local/core-engine/.env`; never point it at
production. Worker process-crash tests require capture SMTP on the configured
loopback port; it must never relay externally. Tests replace service credentials and block external sockets.

Run pytest, Mypy, Ruff, Bandit, secret scans and Python builds. See
[testing](../../docs/testing.md), [API](../../docs/api/README.md),
[architecture](../../docs/architecture.md) and
[operations](../../docs/core-engine-operations.md) and the dated
[current release evidence](../../docs/evidence/voice-release-20261025.md).

## Records and local transcript exports

Owner-session/CSRF POST routes expose dedicated bounded schemas rather than raw
state. Typed settings own byte limits and safe attachment filenames. Counts and
rows for each collection share one database statement snapshot. Local transcript
artifacts require an ended same-tenant call; redaction uses tenant/row locks and
a durable tombstone. Success audits exclude content and credentials. Separate
collections can change independently; the records report is not a full backup.
See [API contracts](../../docs/api/README.md) and
[current verification](../../docs/evidence/tenant-export-release-20261015.md).
