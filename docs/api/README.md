# HTTP, provider and MCP contracts

`core-openapi.json` is the generated contract. Frontend generated types are checked
against it by `npm run test:core-contracts`. Update server schemas first, regenerate
using the configured CLI/type generator, then review both sides.

| Group          | Purpose                               | Boundary                                                     |
| -------------- | ------------------------------------- | ------------------------------------------------------------ |
| Health         | Liveness/schema readiness             | Minimal public status, no business data                      |
| Authentication | OIDC/session/logout                   | State/PKCE/nonce/signature and trusted subject binding       |
| State/bookings | Availability and confirmed operations | Tenant role/capability; CSRF on session mutations            |
| Knowledge      | Import/search/revise/delete           | Tenant, size/parser limits and revisions                     |
| Jobs           | Inspect/replay/reconcile              | Management scope; unknown delivery cannot be blindly retried |
| Evaluations    | Maintained business cases             | Authorized isolated records and cancellation cleanup         |
| Native calls   | Intent, bind, lifecycle/tools         | Owner plus bounded capability; platform authentication first |
| MCP            | Business/management read/write tools  | Separate scopes and protocol-valid errors                    |

Exact methods/routes/schemas/errors belong to OpenAPI and the provider specification.
Health success does not establish user authorization. Never expose management or
provider keys in browser variables.

Use stable operation IDs on retries, new IDs when intent changes, expected revisions
and timezone-aware appointments. Present pending/conflict/unknown outcomes explicitly.
Bound bodies, timeouts and response lists. Do not retry ambiguous provider writes or
retired calls. Retell verifies raw-body signatures; Vapi verifies server credentials.
Opt-in metadata capability handling follows platform verification. See
[native interoperability](../provider-interoperability-spec.md).
