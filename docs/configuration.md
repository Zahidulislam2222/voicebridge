# Configuration, environments and change control

Configuration has one owner per value. Backend environment values enter typed
Pydantic settings; browser values enter the typed public settings module; maintained
business content and provider profiles enter validated data files. API/protocol
syntax belongs to the named protocol/contracts boundary. Constructors do not invent
provider defaults. `.env.example` contains safe names/examples, never credentials.

| Boundary | Owner | Release requirement |
| --- | --- | --- |
| Backend/process environment | `apps/api/voicebridge/settings.py` | Validation, complete environment examples, secret separation |
| Browser/public environment | `apps/web/src/config/settings.ts` | Same-origin session settings; no private key in a browser bundle |
| Business copy, services, schedules and knowledge fixtures | `data/core`, validated frontend data | Schema validation, revision review, operational approval |
| Provider voice/agent/model definitions | Validated provider profiles and typed provider settings | Account-specific readback, compatibility, rights and quota review |
| HTTP schemas and route identities | Pydantic contracts and generated OpenAPI/client | Regeneration and server/client drift checks |
| Deployment/runtime controls | Validated release tools/templates | Immutable artifacts, manifest identity, drift and rollback |
| Private credentials | Approved environment/secret storage and ignored recovery records | Actual values protected; scopes, revocation and rotation verified |

## Environment separation

Use isolated development, verification and production identities/databases. Tests
replace credentials and refuse external provider sockets. Browser sessions and
operator capabilities are separate access modes; a local capability must not become
a public owner session. Do not copy a production database into a development system
without approved minimization and access controls.

Every release records provider/profile revision, environment policy, migration
version, artifact digest and rollback compatibility. Environment changes require
the same review as code when they enable delivery, widen origins, change account
scope, raise resource limits or alter data processing. Verify the effective running
configuration, not just a file on disk. A disabled execution policy must remain
visible in operational checks.

## Operator exports

`VB_EXPORT_MAX_BYTES`, `VB_EXPORT_SNAPSHOT_FILENAME` and
`VB_EXPORT_TRANSCRIPT_FILENAME` are typed settings. Attachment names must pass the
safe JSON filename validator. Reports expose record limits, counts and truncation.
Changing these settings does not require business-service edits. The current
bounded records export is not a database backup.

## Secret rotation and recovery

Identify every consumer before rotation, deploy the new scoped value through private
configuration, verify both authorized and rejected paths, then revoke the old value.
Document the rotation date and recovery route privately. Do not publish keys,
sessions, webhook secrets, provider IDs tied to private infrastructure, reset codes,
raw request headers or a credential-bearing deployment profile.

Before publication, scan worktree, staging and Git history; verify private files
are ignored and untracked. Run environment coverage and obvious-secret/configuration
regressions. After an interrupted action, inspect the actual external resource and
saved operation receipt before retrying. See [security](security-model.md),
[operations](operations-runbooks.md) and [testing](testing.md).
