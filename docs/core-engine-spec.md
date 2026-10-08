# Core engine acceptance contract

Stage: local integrated core, test-data business data, external execution disabled.
Written before feature code on 7 October 2026. Application login/OIDC is deferred
at the owner's request. Local operator capabilities still require a server-side
credential; tenant and provider-tool boundaries are mandatory.

## Criteria

- C01 Typed settings reject missing secrets, unsafe exposure and invalid limits;
  every environment variable has a safe example and a single owner.
- C02 PostgreSQL migrations install the schema and preserve existing records;
  restart, backup and isolated restore preserve accepted business operations.
- C03 Booking requires explicit confirmation, supported service, valid future
  timezone-aware slot and contact details. DST gaps/ambiguous wall times fail.
- C04 Concurrent callers cannot reserve overlapping application-controlled slots.
  Repeating an operation returns the same result; changed inputs conflict.
- C05 Calendar creation/cancellation/rescheduling use stable external identities;
  ambiguous writes remain pending reconciliation, never falsely confirmed.
- C06 Confirmed bookings atomically create CRM and follow-up outbox jobs. A separate
  worker persists attempts, leases, receipts, bounded retries and dead letters.
- C07 Worker death/expired leases cannot silently lose work. Ambiguous non-idempotent
  delivery requires reconciliation; replay cannot manufacture delivery success.
- C08 Retell raw-body signatures and Vapi configured bearer credentials authenticate
  their own envelopes. Calls bind to server-owned tenant/profile/capability records.
- C09 Both provider adapters execute the same availability/booking/knowledge tools;
  duplicates/out-of-order events cannot regress terminal calls or repeat bookings.
- C10 Contacts, calls, appointments, jobs, agent drafts, integrations, knowledge and
  audit are tenant-filtered API records; unauthorized and forged scopes are denied.
- C11 Knowledge revisions support validated text/Markdown/PDF ingestion and deletion,
  PostgreSQL search with sources, stale/absent/conflicting abstention and no tool
  authority from retrieved instructions.
- C12 Versioned deterministic evaluations exercise booking, confirmation, isolation,
  adversarial retrieval and provider parity; acoustic evaluation stays pending.
- C13 Scoped MCP business and management tools reuse the same services, distinguish
  read/write permissions and deny secret access or unapproved provider promotion.
- C14 The dashboard can exercise real local HTTP persistence and readable failures,
  preserving the published test-data local until a separately gated release.
- C15 Real connector transports have explicit execution gates and typed configuration;
  Vapi access has an explicit owner-resolution gate. The earlier denial is now
  resolved for read-only assistant inventory by a support-approved HTTPX request;
  real voice execution remains separately gated.
- C16 Local n8n workflow routes test-data confirmations into Mailpit, with durable
  job outcomes and no external recipients or SMTP relay.
- C17 OpenAPI/client drift, configuration/secret regression, backend/frontend tests,
  types, lint, security, package/build and real HTTP/UI flows pass with evidence.
- C18 Current run/restore/recovery guides, dossier and checkpoint reflect actual
  implementation; an independent fresh-context review has no blocking findings.

Full roadmap criteria that require real calls, voice rights/listening, commercial
licensing, production OAuth/authentication, public release, legal review, observed
uptime or future million-scale evidence remain separate. Local success does not
close those criteria. No new payment, real call, message or live deployment follows
from this implementation contract.

## Configuration inventory

| Family                                                          | Owner                                                 |
| --------------------------------------------------------------- | ----------------------------------------------------- |
| Database URL, pool, bind, CORS, limits, worker leases/backoff   | typed Settings / environment                          |
| Operator, business MCP, management MCP and webhook secrets      | ignored environment; CREDENTIALS recovery             |
| Calendar/CRM/voice URLs, API paths, versions, models, deadlines | typed ProviderSettings / environment                  |
| Service duration, hours, timezone, branding and booking copy    | validated data/core/business.json                     |
| Tool names and provider envelope/header constants               | protocol modules                                      |
| Knowledge limits, search language, freshness and answer limits  | typed Settings                                        |
| Prompt, follow-up template, evaluations and provider profiles   | validated data/config files                           |
| SMTP sink and n8n webhook endpoints/auth                        | typed Settings; local-only execution                  |
| Prices and approved usage                                       | maintained data; no approved real usage at this stage |

## Research basis

- [FastAPI application organization](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [SQLAlchemy transactions and row locking](https://docs.sqlalchemy.org/en/20/orm/session_api.html)
- [PostgreSQL queue locking](https://www.postgresql.org/docs/current/sql-select.html)
- [Retell webhook verification](https://docs.retellai.com/features/secure-webhook)
- [Vapi authentication](https://docs.vapi.ai/server-url/server-authentication)
- [Vapi function response envelopes](https://docs.vapi.ai/tools/custom-tools)
- [Calendar deterministic event IDs](https://developers.google.com/workspace/calendar/api/guides/create-events)
- [HubSpot contacts](https://developers.hubspot.com/docs/api-reference/crm-contacts-v3/guide)
- [MCP tool contract](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

Package versions must be checked against PyPI before installation and frozen into
a reproducible lock. Requests and external writes must never expose credentials in
logs, command arguments, browser bundles or public evidence.
