# Deployment templates

Release tools populate frontend/engine templates from private deployment settings.
Never write actual credentials into committed templates. The backend Docker context
allowlists runtime/data/migration inputs and excludes private records.

Tools: `tools/prepare-frontend-release.mjs` and `tools/prepare-engine-release.mjs`.
Generated releases include immutable artifacts/manifests. Required order: inventory/
drift -> local snapshot/change/gates -> migration/rollback review -> deploy -> real
acceptance -> local/live hashes. Production is a deployment target, not an editor.
Preserve unrelated containers/gateway/database state; never delete working volumes.

The current single-business release passed backend 16/16 and frontend 7/7
local/live file parity checks, with a valid database backup and readiness checks.
The earlier unjoined Retell call ended and its slot is clear. Creation remains
disabled while separately approved GET-only recovery is enabled for the owner.
Any later call requires fresh free-entitlement and owner acceptance checks.
Unrestricted external mail remains disabled. Treat these as
release-specific results; repeat drift, backup, security, behavioral and parity
checks for every later deployment. The shared server is one failure domain and
does not establish the [future uptime objective](../docs/reliability.md).

See [current release evidence](../docs/evidence/tenant-export-release-20261015.md),
[frontend deployment](../docs/frontend-deployment.md),
[engine operations](../docs/core-engine-operations.md),
[reliability](../docs/reliability.md) and [runbooks](../docs/operations-runbooks.md).

The current export release and configuration boundaries are documented in
[release evidence](../docs/evidence/tenant-export-release-20261015.md),
[configuration](../docs/configuration.md), [providers](../docs/integrations.md)
and [monitoring](../docs/monitoring.md). Future infrastructure changes require
staged capacity, security, cost and recovery acceptance before activation.
