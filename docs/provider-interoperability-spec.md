# Provider event interoperability acceptance

This is a focused extension of pilot R08. It does not authorize chargeable calls.

- [x] P01 Opt-in capability metadata is read only after provider authentication.
      A supplied header has precedence; missing, wrong or unregistered call/agent
      capabilities fail closed. The tenant never comes from provider metadata.
- [x] P02 Retell ended/analyzed transcript objects and Vapi end-report artifact
      messages normalize to durable assistant/user entries. System/tool messages
      are excluded, malformed data is rejected, and the request body limit applies.
- [x] P03 Vapi status-update ended retires a call before the end-report arrives.
      A later valid end-report may persist its transcript; stale starts cannot reopen
      the call and tools cannot run on an ended call.
- [x] P04 Duplicates and empty/late reports preserve the first nonempty final
      transcript. Live partial transcripts are not presented as final evidence.
- [x] P05 Real HTTP regressions prove both providers' signatures/credentials,
      metadata/header boundaries, call binding, retirement and durable transcripts.
- [x] P06 Local/live source snapshots precede edits; tests, types, lint, security,
      package/build, fresh-context review and deployed parity pass before publication.
- [x] P07 An owner can prepare a bounded expiring call intent using the maintained
      provider profile; the server creates its capability before any native call.
      Preparing an intent makes no provider request and cannot incur usage charges.
- [x] P08 An intent binds to exactly one returned native call ID. Same-ID binding
      retries are idempotent, including after the preparation deadline; this returns
      only the existing call ID and never a new capability. Expiry rejects an initial
      binding. Unknown, cross-tenant and different-ID retries fail closed. A call's
      agent/provider/tenant comes from the trusted intent.
- [ ] P09 Native preparation passes the capability into Retell metadata or Vapi
      per-call server headers, binds the native ID, and only then joins audio. This
      avoids a race between a provider's call-start event and engine registration.

Native configuration preparation is separate from chargeable execution: it must
preserve existing assistants, create at most one dedicated profile per provider,
save request fingerprints before creation, and reconcile an unknown outcome
through native inventory before any retry. Provider IDs are private validated
profile data mounted read-only. A new immutable release preserves the existing
database, identity encryption key and credentials; rollback and unrelated-service
preservation must be verified before live publication.

The metadata wire field belongs to the protocol module. The opt-in policy belongs
to typed settings and `.env.example`, defaulting off. Native call preparation must
register the returned call ID with the engine and attach its server-owned
capability before joining audio. Provider keys/capabilities remain private.

Official references checked before implementation:

- https://docs.retellai.com/features/webhook-overview
- https://docs.retellai.com/api-references/update-call
- https://docs.vapi.ai/server-url/events

Retell allows updating registered-call metadata before audio joins. Vapi's official
web SDK 2.7.1 creates `/call/web` before joining Daily audio; its update-call DTO
only supports renaming, so it cannot repair capability metadata afterward. Prepare
the capability first and supply per-call server headers through assistant overrides.
The SDK exposes reconnect for joining an already-created web call. Actual provider
payload acceptance and audio remain live-test gates. An event contract test alone
is not proof of a live provider call.

Compose retains raw short mount strings in x-runtime extensions. Deployment checks must normalize only the exact new readonly profile mount there, retain whole-configuration equality, and test rejection of writable/unrelated extension changes. An explicit preflight-only resume is permitted only after a recorded no-process-mutation stage and independent current old/candidate/archive/image parity; never retry an unknown process-upgrade outcome.

The actual retained x-runtime mount uses the template-relative ./provider-profiles.json source, while resolved service mounts use absolute release paths. Verify the checker against saved real platform output before resuming, rather than relying on structural fixtures alone.

A free post-upgrade public probe checks readiness200, unauthenticated state/intent401, invalid Retell/Vapi credentials401, and correctly authenticated but unregistered test-data calls403. It must contact only the selected owned engine origin, refuse redirects, persist only status/error evidence, and never create a native call, join audio or store a test-data call.

P01–P08 accepted for the measured authenticated pilot scope:144backend/23focused checks, native configuration readback,14source/12release hash parity, reviewed03deployment and public auth-denial checks. P09 remains open: no native call creation/bind/audio run has occurred.
