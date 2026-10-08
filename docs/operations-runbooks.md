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
