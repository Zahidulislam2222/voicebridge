# Owner snapshot and local transcript export acceptance

This closes the existing local export/artifact isolation gap in P3.3. It adds
bounded downloads from the authenticated single-business engine. It does not
fetch provider recordings, make a full backup, erase downloaded copies or
establish wider privacy/legal readiness. Records in different collections may
change during generation; the download is a bounded current records report.

Before implementation, verify the deployed18 baseline and preserve its snapshot.
Secrets remain in the existing settings/secret boundary. New byte limits and safe
attachment filenames belong in typed settings and .env.example. Maintained UI
copy belongs in validated frontend data. Stable endpoint/schema identities belong
in the existing protocol/contracts boundary. No new dependency is planned.

- [x] E01 Owner session and CSRF-protected POST generate a dedicated safe JSON
  snapshot schema: bounded rows, deterministic ordering, true counts, truncation
  metadata and a typed serialized-byte cap. Calls contain summaries only; no
  transcript, credential, capability/grant, raw job payload, provider URL,
  private Record or AuthSession is exported.
- [x] E02 Two real local OIDC test tenants with distinct fake markers cannot read
  each other's records, jobs, snapshots or local transcript artifacts. Caller
  tenant fields/query selectors fail; foreign and missing call IDs return the
  same404. Inspect actual response bodies for own/foreign/private markers.
- [x] E03 Anonymous, viewer/operator, expired/revoked/logout, missing-CSRF and
  untrusted-origin requests fail before generating a download. Existing API
  authorization and configuration/contract checks remain green.
- [x] E04 Transcript export reads only the same tenant's ended call. Active calls
  fail; empty transcripts are explicit; a redaction tombstone yields an empty
  redacted result even if stale text remains stored. Lock ordering with redaction
  and late provider events is exercised. General snapshot exports never include
  any transcript; the ordinary state view also honors tombstones.
- [x] E05 Safe server-controlled attachment names, JSON content type, no-store
  and nosniff headers are verified. Serialized output over the configured byte
  cap fails predictably; no arbitrary filesystem access or provider request.
- [x] E06 Successful generation/access creates a sanitized audit without content,
  credentials or arbitrary caller names. Rejected requests produce no success
  audit; existing auth-denial policy remains explicit. Server generation does
  not prove the browser saved a file.
- [x] E07 Owner UI downloads the actual API payload; session loss/logout/unmount
  aborts or discards late results, Blob URLs are revoked, and data is not persisted
  to localStorage/logs. Browser tests inspect downloaded JSON and cancellation.
- [x] E08 Generated OpenAPI/client types, full tests/types/lint/security/build,
  fresh independent review, local-first deployment/parity and a bounded live
  owner HTTP check pass. Original roadmap counts advance only from evidence.

E01–E07 have local HTTP/PostgreSQL and exact packaged-browser evidence. E08 passed release parity and actual owner HTTPS verification with independent approval. See docs/evidence/tenant-export-release-20261015.md.
