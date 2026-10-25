# Deployment templates

Release tools populate frontend/engine templates from private deployment settings.
Never write actual credentials into committed templates. The backend Docker context
allowlists runtime/data/migration inputs and excludes private records.

Tools: `tools/prepare-frontend-release.mjs` and `tools/prepare-engine-release.mjs`.
Generated releases include immutable artifacts/manifests. Required order: inventory/
drift -> local snapshot/change/gates -> migration/rollback review -> deploy -> real
acceptance -> local/live hashes. Production is a deployment target, not an editor.
Preserve unrelated containers/gateway/database state; never delete working volumes.

The current single-business release (backend 23, 2026-10-25) passed backend
16/16 file and 15/15 image-module parity and frontend 7/7 parity, with a database
backup, readiness and preservation of 77 unrelated containers. The guard admits
owner voice creation together with GET-only recovery only under an explicit voice
approval, and native limit changes only when they equal an approval bounded by the
typed settings maximums. Release 23 also carried a rotated Google Calendar token,
admitted only under an explicit token-rotation approval. Its free-credit receipt has
expired, so calls stay refused; a later call needs a fresh billing check carried by a new immutable release.
Unrestricted external mail remains disabled. Treat these as
release-specific results; repeat drift, backup, security, behavioral and parity
checks for every later deployment. The shared server is one failure domain and
does not establish the [future uptime objective](../docs/reliability.md).

See [current release evidence](../docs/evidence/voice-calls-20261025.md),
[frontend deployment](../docs/frontend-deployment.md),
[engine operations](../docs/core-engine-operations.md),
[reliability](../docs/reliability.md) and [runbooks](../docs/operations-runbooks.md).

The current release and configuration boundaries are documented in
[release evidence](../docs/evidence/voice-calls-20261025.md),
[configuration](../docs/configuration.md), [providers](../docs/integrations.md)
and [monitoring](../docs/monitoring.md). Future infrastructure changes require
staged capacity, security, cost and recovery acceptance before activation.
