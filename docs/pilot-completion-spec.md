# Single-business pilot completion

Requested 2026-10-13. Finish the single-business release on the existing server,
preferring verified free/free-tier services. Million-scale workloads remain future
acceptance stages. Earlier evidence is historical until explicitly rechecked.

## Acceptance

- [x] F01 Current local gates, live source drift and service health are inspected;
      recovery evidence is saved before mutations and existing services are preserved.
- [x] F02 Calendar, CRM, voice and delivery execution have independent,
      default-disabled typed configuration. Enabling a free connector cannot enable
      voice usage or arbitrary recipients. Examples and configuration tests cover it.
- [x] F03 A confirmed owner-only test booking reaches the selected existing Google
      Calendar; readback matches, retries reconcile, and cancel/reschedule are checked.
- [x] F04 The approved test contact reaches the existing CRM, with readback and
      visible authorization/failure/recovery states.
- [x] F05 An explicitly authorized owner recipient receives a booking follow-up;
      the receipt and worker restart behavior are verified without blind resends.
- [x] F06 A synthetic custom voice has a recorded creation method, settings,
      attribution and permitted-use boundary; free balances and overage behavior are
      verified before generation. No commercial license is inferred from a free plan.
- [ ] F07 Retell and Vapi each prepare/bind a bounded native call before audio,
      complete grounded lookup and booking, and persist transcript/outcome. Owner
      listening checks, interruption and handoff results are recorded.
- [ ] F08 Operator UI shows durable results, source-backed answers, provider and
      delivery failures, usage limits and integration readiness without unsupported claims.
      Acceptance: the owner can reload and see a sanitized, tenant/owner-scoped native
      operation ID and state, including UNKNOWN with a manual-reconciliation instruction.
      No secret or media grant appears in that record; a nonterminal operation disables
      another create in the UI while the server remains authoritative. Show configured
      native duration/concurrency and page display limit, dated free-entitlement
      readiness or stale/unverified state, and explicitly label captured versus
      externally delivered follow-ups. Mark settings flags as configuration, not
      connectivity proof. A BOUND call is resumable only while its binding and media
      grant remain valid; otherwise show manual reconciliation. Losing the owner
      session while create/join is pending or media is active aborts/stops the media.
      Exercise the authenticated UI with real persisted state.
- [ ] F09 Scoped MCP business/management flows and denial cases are exercised in
      actual compatible clients; unsupported surfaces stay explicitly incomplete.
- [ ] F10 Applicable privacy, authorization, retention/deletion, security,
      observability, restore and rollback requirements have scoped evidence.
- [ ] F11 Tests, types, lint, security, dependency/configuration audit and builds
      pass; a fresh context reviews the final implementation against these criteria.
- [ ] F12 Approved local artifacts deploy after drift checks; every changed file
      matches local/live hashes, actual authenticated live journeys pass, and final
      evidence records unresolved limits without claiming future capacity or uptime.

## Configuration inventory

| Values                                                            | Owner                                                                 |
| ----------------------------------------------------------------- | --------------------------------------------------------------------- |
| Separate calendar/CRM execution permissions                       | Typed provider settings/environment; disabled defaults                |
| Follow-up transport, allowed recipients, SMTP TLS/authentication  | Typed delivery settings/environment; secrets in ignored recovery file |
| Provider URLs, models, API versions, retry/deadline/budget limits | Existing typed settings and validated provider profiles               |
| Voice brief, attribution, consent text, scenario content          | Validated maintained data; private provider IDs stay private          |
| Integration readiness and operator copy                           | Allowlisted API contract and maintained frontend data                 |
| Release paths, image identity, resource limits                    | Existing private deployment profiles and release manifests            |

Free-credit calls require verified current balances and no-charge boundaries.
An uncertain billable action remains blocked until the exact-cost warning and
fresh-turn approval required by the owner's money rule. A missing gate remains
open; test-data or contract success cannot replace a real external receipt.

## Worker egress correction acceptance

The first real deployed calendar job exposed an internal-only worker network.
The correction must keep database, mailbox and observer private, add the existing
egress network only to the worker through a default-disabled deployment setting,
and require explicit approval of that exact layout change. No additional ports or
networks may appear. A configuration-only upgrade may preserve only explicitly
listed calendar jobs with a known pre-send failure, dead status, no active lease
and no receipt; active or ambiguous effects still block it. This state filter does
not prove a calendar write never happened. Jobs remain parked for stable-ID
readback/reconciliation before an authenticated retry. Reusing an owned image
archive requires exact image, source and archive-digest equality and remote hash
verification. Fresh review, local tests, live snapshots and final parity apply.

## Native call acceptance

The owner selects only a dedicated provider and a stable operation key. Server
configuration chooses the accepted assistant revision, voice, model, tools,
duration, billing entitlement and web endpoints. An owner/CSRF-checked create
operation records encrypted recovery data and an account-wide one-call lease
before one provider create request. Its capability reaches Retell call metadata
or every Vapi event/tool server header. The returned provider ID and media grant
are saved durably, then the exact existing intent is bound and committed before
the browser receives a media-only grant. Retries return the same bound operation;
ambiguous creation stays UNKNOWN and blocks automatic recreation. Cross-role,
cross-tenant, expired, concurrent, stale-entitlement, unconfigured and disabled
requests fail closed. The browser never receives an account key, webhook secret,
business capability, or full assistant configuration.

Retell v3 server creation and compatibility-client media join, and Vapi server
web-call creation and SDK reconnect, are version-pinned and tested against
official contracts. A bounded owner-only live sample per provider must prove
actual create, bind, join, tool/webhook authorization, grounded answer, booking
and terminal transcript; cost is checked against verified finite free credits
and BYOK inventory. A microphone permission, call or provider response error is
recorded as an incomplete criterion rather than simulated success. Native calls
must remain disabled in the live runtime until all pre-call gates pass.
For Vapi, the maintained assistant request and live assistant readback must
explicitly match recording disabled, detailed logging disabled, PCAP disabled,
and transcript enabled. Its call record persists separately and requires a
post-test deletion/readback procedure. For Retell, read back the reviewed
one-day storage setting and opening AI/recording notice before a live call.
Local and provider transcript deletion, including backup-restore replay
protection, remains a separate F10 acceptance gate.
For the scoped owner-only test, a local redaction action must require the owner
session and CSRF, accept only an ended call in the owner's tenant, clear the
stored transcript idempotently and leave a tenant-scoped tombstone so later
provider events cannot restore it. Cross-tenant or active-call redaction must
fail closed. This local action does not claim to delete provider artifacts or
remove historical backup copies; those need separate verified steps.
The native request template, pinned Retell readback and fresh free-credit entitlement
are separate ignored release files mounted read-only into the API process only;
worker, observer and unrelated services receive no new mounts. The deployment
guard must reject any other mount, network, port or service change.
Each frozen backend release must load and validate its complete private runtime
environment before finalization. External delivery disabled with SMTP transport
is invalid; voice-test releases use capture transport and no recipients.
Enabling voice in a deployment requires a separate explicit boolean approval in
the ignored upgrade configuration, an exact approved execution policy with
external follow-up disabled, capture transport and no recipients, and the
three approved native API mounts. The upgrade guard rejects voice if any one
of those conditions is absent; all previous business-only defaults remain safe.
Changing the provider profile requires a separate exact SHA-256 approval of the
new private profile file; no other persistent or security file may change.
Release preparation must explicitly select the reviewed private provider-profile
source when live provider IDs/voices differ from the public sample profile, and
verify its frozen bytes against that approval before deployment.
The published single-file HTML must contain both media clients or otherwise
serve every generated chunk with matching content policy; opening the actual
release must load each client without a missing asset or CSP violation. During
owner voice booking tests, external follow-up delivery must be disabled because
the one approved owner email test has already been consumed.
Leaving the page, losing the owner session, or unmounting while microphone,
create, or media join is pending must prevent a late media session; a join that
resolves after cleanup is stopped. A deferred-create/deferred-join regression
proves this behavior before live acceptance.
