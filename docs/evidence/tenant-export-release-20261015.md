# Owner exports — 2026-10-15

Backend `20261015-tenant-exports-19` and frontend `20261015-tenant-exports-10`
are deployed. All 16 backend files,15 image source modules and 7 frontend files
match local/live. The promotion preserved 57 neighboring containers and 13 gateway
files. A 36,249-byte PostgreSQL backup passed format/digest checks; this particular
backup was not restored.

Owner-session and CSRF-protected JSON POST downloads provide bounded current
records and ended-call local transcripts. A dedicated projected schema excludes
raw job payloads, credentials, private records and call transcripts from the
records report. Each collection's rows and count share a statement snapshot;
collections can change independently. Counts/truncation and a typed serialized
byte cap make the scope explicit. This report is not a full backup.

Transcript exports respect tenant/row locks and durable redaction tombstones,
even if stale text exists or late provider events arrive. Server-controlled
attachment names, JSON/no-store/nosniff headers and sanitized success audits are
verified. Downloads cannot erase provider copies or files already saved.

| Gate | Verified local result |
| --- | --- |
| Acceptance | E01–E08 accepted; independent implementation, frozen candidate and live evidence approval |
| Backend | 252/252 full checks; focused export/redaction21; independent export18 |
| Frontend | 108 tests, types, lint, final format, generated contract and production build passed |
| Security | Bandit0; Semgrep79 rules/15 runtime modules0 findings/errors; source Gitleaks0; installed edit bridge passed |
| Configuration | 221 public files/37 saved private values0 matches, private staging0, full environment example coverage |
| Packaging | Wheel/sdist and tagged image built; image source15/15 identical |
| Browser | Exact frozen candidate21 routes/login,0 JavaScript/CSP/external errors; nine export scenarios passed |
| Downloads | Three fake JSON attachments inspected; logout/unmount/request and polling denial produce no stale download; all created Blob URLs revoked; viewer/active controls absent |
| Review | Independent backend and frontend implementation approval; exact candidate and live evidence approved |
| Drift | Before editing, deployed backend15 payloads/frontend7 files matched the saved baseline |

No new dependency, provider recording fetch, real call, external email, paid
resource, GitHub push or Google Doc/PDF update occurred. Voice creation and
external mail stay disabled with capture transport and no recipients. Broader
privacy, voice, monitoring, capacity and remaining roadmap gates stay open.

Actual owner HTTPS returned200 for both exports (11481-byte records report and
170-byte transcript artifact), with two fresh durable audit entries and unchanged
three appointments, three contacts, one historical call and ten jobs. The live
transcript is empty and unredacted; nonempty, redaction and foreign-tenant cases
are demonstrated locally. Ten public HTTPS checks verified exact HTML/artwork/CSP,
readiness, anonymous export401 and private-path404. All 21 actual routes passed
with 0 JavaScript/CSP/external-request errors. The signed-in owner UI rendered one
records and one ended-transcript control, with creation controls absent and0
JavaScript errors (two warnings); navigation used programmatic dispatch after a
physical actionability timeout. Saved browser attachments were inspected in the
nine controlled journeys; no live browser-save claim is made.

Original P3.3 is accepted for the existing bounded tenant export/local artifact
boundary. Roadmap26/50 implementation,0/30 readiness;54 requirements remain open.
Provider recordings, broader privacy and live multitenant claims remain outside
this evidence. The earlier MCP denial release is preserved in
[mcp-denial-release-20261015.md](mcp-denial-release-20261015.md).
