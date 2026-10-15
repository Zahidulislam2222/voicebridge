# Provider and business integration contracts

VoiceBridge shares booking, knowledge, contact and job services across its browser,
Retell, Vapi and scoped MCP boundaries. Provider-specific adapters authenticate and
validate envelopes before invoking those services. The provider does not choose
the trusted tenant, role or action scope.

| Integration | Contract and controls | Current evidence / next acceptance |
| --- | --- | --- |
| Google identity | OIDC code flow, PKCE/state/nonce, signature/issuer/audience/expiry, trusted subject binding, revocable session and CSRF | Owner login/logout/denial verified; broader onboarding/MFA/recovery remains staged |
| Google Calendar | Frozen booking intent, stable external identity, revision/conflict checks and receipt reconciliation | Bounded owner booking/cancellation/readback; wider customer and voice-originated journeys remain open |
| CRM | Tenant contact/booking linkage, durable job, known failure vs unknown delivery | Bounded owner receipt; ambiguous-write recovery needs provider-specific proof |
| Follow-ups | Capture, SMTP or n8n transport selected through settings; explicit recipient policy | One earlier owner email receipt; current general external email disabled |
| Retell | Platform signature, trusted agent/call binding, active-call capability and terminal retirement | Dedicated configuration and adapter checks; completed conversation/listening still open |
| Vapi | Platform credentials, trusted assistant/call binding and validated tool envelopes | Dedicated configuration/read access and adapter checks; native audio acceptance still open |
| ElevenLabs | Maintained voice design/profile, licensed source, provider/account compatibility | Voice method/settings/rights recorded; commercial portability and comparative listening require separate acceptance |
| MCP | Distinct business/management read/write capabilities, narrow tool inventory, tenant checks and sanitized denials | Official SDK reads and actual denial audits; native assistant-client and approved provider promotion remain separate |
| n8n | Operation/receipt identity, durable business worker, authenticated bounded delivery endpoint | Maintained workflow and local execution evidence; full workflow crash/duplicate-delivery rehearsal remains open |

## Retry and lifecycle policy

A timeout is not proof that a remote write failed. Reuse a stable operation identity
only for the same confirmed intent, use expected revisions, and reconcile external
receipts before retrying an ambiguous operation. Known failed/dead work may be
replayed through its authorized contract; unknown delivery is not automatically
successful or safe to resend. Ended calls lose tool authority.

Owner terminal recovery uses GET-only provider verification for the exact bound
operation. It does not create or stop a provider call. An unknown creation without
a returned provider ID needs manual reconciliation. Transcript redaction/export
covers local records; provider recordings and historical backups need independent
retention/deletion proof.

## Activation and dependency review

Before enabling a provider, confirm current API/schema revisions, account and
region, voice/media rights, contractual data roles, subprocessors, retention,
quotas, concurrency/start/tool limits, permitted recipients and spend controls.
Record provider outage, timeout, duplicate, out-of-order and malformed-envelope
behavior. Keep bounded human handoff and explicit unavailable outcomes.

A code adapter or account readback does not establish audio quality, phone delivery,
end-to-end booking or large-scale capacity. The release sequence and evidence live
in [the roadmap](roadmap.md), [interoperability criteria](provider-interoperability-spec.md)
and [current verification](evidence/tenant-export-release-20261015.md).
