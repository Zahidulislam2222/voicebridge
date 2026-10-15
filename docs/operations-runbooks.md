# Operational runbooks

Use approved targets and credentials. Inspect actual state before replaying an
interrupted action; a timestamp does not prove that an action failed.

## API or deployment failure

Identify active release/image, gateway and dependencies. Inspect latency/errors,
database pools/locks and resource signals. Compare live/local artifacts and save a
before snapshot. Restore a pinned compatible release when needed; verify readiness,
business flows and hash parity. Record interval, observation gaps and root cause.

## Backlog or unknown delivery

Inspect revision, immutable intent, lease, attempts and receipt. Preserve user intent.
Replay only known failed/dead work according to contract. Reconcile stable calendar
IDs. Ambiguous CRM/email remains unknown until receipt evidence supports recovery.
Never resend a confirmation merely because a process restarted.

Distinguish captured follow-ups from externally delivered receipts. A disabled
delivery switch is a configuration state, not evidence that a vendor accepted a
message. Confirm provider receipts before moving unknown work to completed.

## Provider denial/quota

Stop identical rejected requests and retain sanitized status/type/correlation.
Verify documented authentication, application headers and approved quotas/account
state. Follow official support guidance. Do not evade security, enable billing or
replace resources to force access. Apply bounded admission and handoff.

## Security/privacy incident

Contain routes/credentials, revoke sessions and rotate compromised values. Assess
tenant/data/provider scope and preserve private audit evidence. Involve assigned
security/privacy owners and assess actual notification duties/deadlines. Never
publish participant data or secrets. Add corrective regression tests.

For transcript erasure, confirm the caller's tenant and authority, local tombstone,
provider artifact deletion and historical-backup replay policy separately. A
local redaction result alone is not an end-to-end deletion receipt. Preserve a
minimal private audit trail without retaining deleted content.

## Restore/restart

Verify backup integrity/encryption/keys; restore separately and compare records,
migrations and business flows. Measure RPO/RTO before traffic switch. Inspect
pending/unknown work before worker start. Never delete working volumes or prune
shared infrastructure as recovery.

## Records

Record intended action, baseline, recovery, commands/action IDs, outcome, unresolved
state and next step. Private evidence stays private. Public results derive from
verified evidence. Google Docs keep stable identity; canonical PDFs change only
after a valid temporary export is ready.

## Owner export investigation

Verify current session/role, CSRF/origin, selected tenant and response byte/row
limits. A report with truncation is a bounded current view; use an approved backup
or rights-request process for a different purpose. For transcript access, inspect
ended state, local redaction tombstone and sanitized audit. Do not request provider
recordings or recreate a call to satisfy a local download problem. Treat files
already saved by a recipient as a separate access/retention responsibility.

## Failed or interrupted image publication

Inspect the saved deployment phase, active pointer/image/labels and manifest before
retrying. Validate archive digest, saved release tag, image/config identity and
source/payload hashes before upload or process quiesce. Preserve a failed immutable
candidate and choose a distinct corrected release; do not relabel live state to
hide a packaging failure. Verify owned process health and unrelated-resource
preservation after activation or compensating rollback.

## GitHub and public-document delivery

Verify owner/author, secret exclusions and the exact staged tree. Push a reviewed
branch, require protected checks, merge through the permitted workflow, then inspect
remote commit/tree and post-merge CI. Keep repository metadata and all README links
consistent with current evidence. Publish public summaries, not raw deployment
profiles, credential recovery, browser captures or private customer records.

After repository verification, compare the existing native Google Doc. Update the
same ID with revision guards, latest relevant facts first, preserving earlier
content and native structure. Export a temporary PDF, check content/page count and
layout plus privacy/format/hash, then replace the canonical file atomically.
Record interrupted/unknown writes before retrying; Google Doc identity, sharing
and working prior PDF remain protected through this process.
