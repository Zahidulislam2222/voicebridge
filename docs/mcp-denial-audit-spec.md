# MCP denial audit acceptance

Scope: the existing single-business, static-capability MCP endpoints. This adds
sanitized durable denial evidence without changing tool permissions, bearer
credentials, provider promotion policy or native-client compatibility claims.
The [MCP authorization specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/authorization.mdx)
defines transport authentication separately from tool execution errors.

- [x] A01 Missing/wrong credentials and cross-surface credentials retain HTTP401
  and write a tenant-scoped authorization denial without storing credentials.
  Unavailable audit storage returns a sanitized503 and never allows execution.
- [x] A02 Unavailable tools, read-only mutations, foreign-tenant arguments,
  secret-read attempts and unapproved promotion/spending are denied and audited;
  no external operation or business mutation occurs.
- [x] A03 Audit fields use fixed surface, capability, recognized tool and reason
  vocabularies. Request IDs, unknown tool strings, arguments, exception details,
  credentials and caller-supplied tenant identifiers are absent from records.
- [x] A04 A typed configurable per-minute budget bounds audit rows independently
  for each surface/capability bucket. Overflow produces one suppression marker
  and cumulative durable counts across minute rollover; concurrency cannot exceed
  the configured cap. Denial locks are separate from business transaction locks.
- [x] A05 Successful allowed reads add no denial; HTTP tests use real isolated
  PostgreSQL transactions, and full gates plus independent review pass before
  local-first publication with parity and live sanitized denial verification.
- [x] A06 Before upload, the archive restores the exact release tag and immutable
  image/config identity. Missing tags, duplicate/malformed metadata, mismatched
  descriptors and oversized metadata fail locally. Failed candidates remain
  preserved; publication uses a distinct corrected immutable release.

This does not establish OAuth/native assistant compatibility, approved provider
promotion, in-call MCP use, durable long-term log retention, or complete P9 delivery.

All six scoped criteria are verified in the [audit18 release evidence](evidence/mcp-denial-release-20261015.md).
