# Local integrated core verification

Historical local-core acceptance; later deployment/identity/provider results are in
[current deployment evidence](pilot-verification.md). Counts below remain tied to
this earlier stage.

Scope: the eighteen criteria in [the core contract](../core-engine-spec.md), using
test-data business data and disabled real-provider execution. This does not close
the eighty broader build-plan criteria. All eighteen local criteria have acceptance
evidence. The fresh source review found no blocking implementation defects.
Accepted on 8 October 2026, Asia/Dhaka.

## Acceptance evidence

| Criterion | Behavior exercised                                                                                   | Evidence                                                                            |
| --------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| C01       | Typed environment limits, separate capabilities, validated maintained content and provider endpoints | Configuration/provider/product regression tests; private configuration audit        |
| C02       | Frozen migration, real PostgreSQL persistence, populated logical snapshot and isolated restore       | Eleven-table count/hash parity; API restart and worker process recovery             |
| C03       | Explicit consent, service/contact details, future local time, DST/hours validation                   | Booking tests and actual HTTP/browser booking journey                               |
| C04       | Concurrent reservations, stable operation result and changed-payload conflict                        | Sixteen concurrent attempts yield one reservation; idempotency regressions          |
| C05       | Immutable calendar revision, ambiguous write reconciliation and cancellation receipt                 | Calendar fault tests; isolated fixture cleanup, including page size one             |
| C06       | Atomic CRM/follow-up jobs, separate worker, leases/attempts/receipts                                 | Real HTTP → worker → n8n → Mailpit journey; three completed jobs                    |
| C07       | Worker process loss after an external effect and genuine lease expiry                                | Two owned CLI processes killed; one calendar event and no SMTP resend               |
| C08       | Distinct provider authentication and server-owned call scope                                         | Raw-body HMAC, bearer, capability and identity denial tests                         |
| C09       | Shared business tools and terminal lifecycle/idempotency                                             | Both test-data envelopes and out-of-order/duplicate/ended-call regressions          |
| C10       | Protected tenant-filtered records and denial of caller-selected scope                                | HTTP, service, provider and MCP scope tests                                         |
| C11       | Text/Markdown/PDF ingestion, revisions/deletion, sources and abstention                              | Knowledge/PDF tests, conflict-by-fact-key and retrieved-adversarial evaluations     |
| C12       | Nine maintained evaluations with durable, isolated fixture cleanup                                   | Versioned suite and fixture isolation/ambiguous-write/recovery tests                |
| C13       | Four MCP read/write scopes sharing services, valid protocol errors                                   | Official MCP SDK over HTTP; malformed-argument and promotion/scope denials          |
| C14       | Persistent operator HTTP flow and readable failures                                                  | Ten native Chrome journeys, thirty layouts, zero captured errors/external requests  |
| C15       | Disabled real transports, typed connector configuration and resolved Vapi read access                | Execution gate tests; one support-approved inventory GET returned 200               |
| C16       | Authenticated local workflow, single test-data recipient and captured SMTP receipt                   | Three completed jobs, exactly one matching Mailpit message; recipient guard denial  |
| C17       | Tests/types/lint/scans/build/contracts and current real flows                                        | Passing gate results below, current artifact/source hashes and restarted flows      |
| C18       | Run/restore guides, private recovery records and fresh independent review                            | Current records and guides; fresh review 05 has no blocking implementation findings |

## Gate results and limits

The complete backend run passed 107 checks, including two real worker process
recovery checks and four review-04 regressions. Four reproductions failed before
the corrections; ten targeted review-04/evaluation checks passed afterward.
Strict Mypy covers twelve application modules and Ruff passes. Frontend 77 tests,
TypeScript, ESLint and formatting passed after its latest changes.

The frontend build contains 556 modules. Its JavaScript is 1,129.96 KB / 312.33 KB
gzip; the existing 500 KB chunk warning remains. Presentation packaging (three),
release regressions (three) and OpenAPI/client drift (one) pass. Python wheel and
source distribution build pass. A wheel installed into an isolated target imports
that artifact and returns ready 200, protected state 200 and unauthenticated 401;
all twelve packaged source hashes match local source, and the installed artifact
preserves a previous booking and handles the latest malformed MCP case correctly.
the checkout's migration and maintained-data configuration are still required.

The shared edit scanner passed 161 public candidates and six preserved manual
tools. Bandit and Gitleaks report zero findings. Semgrep's full scope reports zero
findings across 140 paths. A bundled-skill analysis timeout was resolved by a
targeted scan with optimization disabled; the final two-file recheck reports zero
findings or timeouts and includes the latest provider code. No rule was suppressed.
Five final changed files also passed the shared scanner. Python's 83 pinned
dependencies and the npm lock audit report zero known vulnerabilities. The Python
audit used the fully pinned lock without dependency resolution after the system
ensurepip helper was unavailable; no pinned dependency was omitted.
The private-value audit compares 163 current source candidates and staged contents
against nineteen saved private values, with zero matches,
no private staging/history and complete typed environment examples. Current typed
secret values were also found in the ignored credential recovery file. This is the
verified audit scope, not a guarantee that every possible secret pattern is known.

The latest populated main database restore preserves eleven tables with matching
row counts and hashes from a 13,664-byte logical snapshot. The working database is
never overwritten. Worker recovery tests use the actual CLI loop with configuration
injected from isolated fixtures; they are process-crash tests, not physical power
loss. Uncertain non-idempotent delivery remains unknown pending receipt recovery.

Capacity tests stay within the maintained resource guard: 1,000 test-data contacts,
four clients and forty requests. They do not prove a million users or calls, zero
downtime, sustained uptime or production performance. Exact latest timing belongs
in the private measurement report; it changes between runs.

Private evidence is retained under the project's ignored evidence/browser/recovery
directories. Public claims exclude credentials, account identifiers and server
details. Real voices/acoustics, voice rights, production OAuth/login, external
delivery, privacy/licensing, public backend release and long-window operations
remain separate gates. The live static presentation was not changed by this work.

Review 05 is a fresh read-only source review; it executed no tests. Its verdict is
"READY FOR LOCAL ACCEPTANCE" with no blocking implementation findings. The full
107-check run, restarted browser/MCP flows and final recovery documentation were
verified separately after its source inspection. This establishes local 18/18
acceptance, not production readiness or working live voice calls.
