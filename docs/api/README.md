# HTTP, provider and MCP contracts

`core-openapi.json` is the generated contract. Frontend generated types are checked
against it by `npm run test:core-contracts`. Update server schemas first, regenerate
using the configured CLI/type generator, then review both sides.

| Group          | Purpose                                                   | Boundary                                                                                               |
| -------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Health         | Liveness/schema readiness                                 | Minimal public status, no business data                                                                |
| Authentication | OIDC/session/logout                                       | State/PKCE/nonce/signature and trusted subject binding                                                 |
| State/bookings | Availability and confirmed operations                     | Tenant role/capability; CSRF on session mutations                                                      |
| Knowledge      | Import/search/revise/delete                               | Tenant, size/parser limits and revisions                                                               |
| Jobs           | Inspect/replay/reconcile                                  | Management scope; unknown delivery cannot be blindly retried                                           |
| Evaluations    | Maintained business cases                                 | Authorized isolated records and cancellation cleanup                                                   |
| Native calls   | Intent, bind, lifecycle/tools, local transcript redaction | Owner plus bounded capability; platform authentication first; deletion is ended-call and tenant scoped |
| Exports        | Bounded records and ended-call local transcript downloads | Owner session and CSRF; typed byte cap, safe attachments, tombstone and success audit |
| MCP            | Business/management read/write tools                      | Separate scopes and protocol-valid errors                                                              |

Exact methods/routes/schemas/errors belong to OpenAPI and the provider specification.
Health success does not establish user authorization. Never expose management or
provider keys in browser variables.

Local transcript redaction records a tombstone so late provider events cannot
restore the deleted local transcript. It does not delete a provider copy or
rewrite an earlier backup; both need separate verified lifecycle procedures.
`POST /api/calls/native/create` requires the owner session and CSRF, a current
free-credit receipt and an exact provider-profile match before any provider request;
it seals the call capability into provider metadata, binds the returned call ID and
returns a minimized expiring media grant. Repeating the same operation ID returns the
existing grant. `POST /api/calls/native/reconcile` requires the owner
session and CSRF, accepts only an exact owned operation and uses a separately
enabled GET-only provider path. It never creates or stops a provider call.
UNKNOWN creation without a returned external ID stays manual. Any later creation
still needs fresh free-entitlement verification. End-to-end audio/tool acceptance
remains open. See [current release evidence](../evidence/voice-release-20261025.md).

Use stable operation IDs on retries, new IDs when intent changes, expected revisions
and timezone-aware appointments. Present pending/conflict/unknown outcomes explicitly.
Bound bodies, timeouts and response lists. Do not retry ambiguous provider writes or
retired calls. Retell verifies raw-body signatures; Vapi verifies server credentials.
Opt-in metadata capability handling follows platform verification. See
[native interoperability](../provider-interoperability-spec.md).

## Owner download contract

`POST /api/exports/snapshot` and
`POST /api/calls/{call_id}/transcript-export` support JSON format. `{"format":"json"}` is explicit; an omitted format
field in `{}` defaults to JSON. Extra fields and other format values are rejected.
Caller tenant selectors fail. Foreign and missing call IDs produce the same404;
active-call artifacts fail409; an oversized serialized export fails413. Responses
use JSON, server-controlled attachment names, no-store and nosniff. The general
report contains summaries only for calls and projected fields for jobs; it excludes
private records, sessions, raw job payloads, capabilities and transcript bodies.
Redacted artifacts explicitly return empty transcript content. Each collection's
count/page is coherent, but the report is not a cross-collection transaction or a
full backup. Audit success means generation, not proof of a saved browser file.
