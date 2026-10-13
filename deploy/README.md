# Deployment templates

Release tools populate frontend/engine templates from private deployment settings.
Never write actual credentials into committed templates. The backend Docker context
allowlists runtime/data/migration inputs and excludes private records.

Tools: `tools/prepare-frontend-release.mjs` and `tools/prepare-engine-release.mjs`.
Generated releases include immutable artifacts/manifests. Required order: inventory/
drift -> local snapshot/change/gates -> migration/rollback review -> deploy -> real
acceptance -> local/live hashes. Production is a deployment target, not an editor.
Preserve unrelated containers/gateway/database state; never delete working volumes.

The current single-business release passed backend 15/15 and frontend 6/6
local/live file parity checks, with a valid database backup and readiness checks.
Voice calls and unrestricted external mail remain disabled. Treat these as
release-specific results; repeat drift, backup, security, behavioral and parity
checks for every later deployment. The shared server is one failure domain and
does not establish the [future uptime objective](../docs/reliability.md).

See [frontend deployment](../docs/frontend-deployment.md),
[engine operations](../docs/core-engine-operations.md),
[reliability](../docs/reliability.md) and [runbooks](../docs/operations-runbooks.md).
