# Deployment templates

Release tools populate frontend/engine templates from private deployment settings.
Never write actual credentials into committed templates. The backend Docker context
allowlists runtime/data/migration inputs and excludes private records.

Tools: `tools/prepare-frontend-release.mjs` and `tools/prepare-engine-release.mjs`.
Generated releases include immutable artifacts/manifests. Required order: inventory/
drift -> local snapshot/change/gates -> migration/rollback review -> deploy -> real
acceptance -> local/live hashes. Production is a deployment target, not an editor.
Preserve unrelated containers/gateway/database state; never delete working volumes.

See [frontend deployment](../docs/frontend-deployment.md),
[engine operations](../docs/core-engine-operations.md),
[reliability](../docs/reliability.md) and [runbooks](../docs/operations-runbooks.md).
