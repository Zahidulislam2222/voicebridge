# Exact-call terminal reconciliation

An abandoned browser join can leave a bound operation occupying the native-call
slot when its terminal webhook is delayed or lost. Checking the exact provider
record must recover that operation without creating, stopping or deleting a call.

Acceptance, recorded before implementation:

- [x] N01 Only the authenticated owner of the operation, in its tenant, with
  CSRF protection can request reconciliation. Unknown operations fail closed.
- [x] N02 Only a durable BOUND operation with an exact local call binding is
  queried. UNKNOWN creates without a returned external ID remain manual; no
  provider inventory search, create, stop, delete or media join is performed.
- [x] N03 The provider GET response must match the bound external ID, agent ID
  and operation metadata, and explicitly report a terminal status. Active,
  registered, malformed, mismatched or unavailable results preserve the slot.
- [x] N04 A verified terminal receipt atomically ends the matching local call,
  marks its operation DONE, clears its encrypted media grant and records one
  audit entry. Repeating reconciliation is idempotent. No provider transcript,
  audio URL, token or complete response is returned or persisted by this action.
- [x] N05 The owner UI offers the check for bound manual-recovery operations,
  including when call creation is disabled. A separate default-disabled typed
  setting enables provider status reads; that transport refuses every method
  except GET and retains destination and Vapi account-ownership checks. It
  refreshes durable status and prevents parallel start/check actions. Session
  denial stops media; UNKNOWN operations keep their manual instructions.
- [x] N06 Regression tests, types, lint, security, builds, a real authenticated
  HTTP flow and an independent review pass before a guarded local-first deploy.

Provider URLs, authorization and request timeouts reuse typed settings; immutable
GET paths and terminal status names have one owner in the protocol module. No
new dependency, secret or paid request is required. The typed setting
`VB_NATIVE_RECONCILIATION_ENABLED` enables only this read-only provider access;
it never enables call creation or audio.

References checked for implementation:

- [Retell Get Call](https://docs.retellai.com/api-references/get-call)
- [Vapi Get Call](https://docs.vapi.ai/api-reference/calls/get/)

This closes a recovery defect only. It does not establish successful audio,
listening, provider deletion, real booking or broader roadmap acceptance.

Accepted for the owner recovery release after final gates, independent review,
authenticated live HTTP/browser checks and16/7local/live file parity. See
[release verification](evidence/reconciliation-release-20261015.md). Real native
audio and the broader roadmap remain outside this acceptance.
