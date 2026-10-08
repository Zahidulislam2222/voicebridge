# Frontend verification — 2026-10-07

**Live:** https://voicebridge.zahidul-islam.com/ — release `20261007-frontend-03`.
Eight complete public pages and twelve operator destinations are published on the
existing shared server. This is frontend acceptance; all 80 broader roadmap
criteria remain unchecked. Derived from the private master dossier.

| Gate                           | Verified result                                                                                                                                                                                                 |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Application tests              | PASS: 70/70, nine Vitest files, including configuration/secret hygiene and CSP-safe schema regressions                                                                                                          |
| Presentation packaging         | PASS: 3/3, compiled application/artwork/local fonts preserved                                                                                                                                                   |
| Release preparation            | PASS: 3/3, exact CSP hashes, typed settings and fail-closed tokens                                                                                                                                              |
| Operational recovery tests     | PASS: 10/10 recovery plus 14/14 native transport/runtime checks under python -O                                                                                                                                 |
| Strict types                   | PASS: tsc --noEmit; build also runs tsc -b                                                                                                                                                                      |
| Lint                           | PASS: ESLint, no warnings                                                                                                                                                                                       |
| Formatting                     | PASS: Prettier                                                                                                                                                                                                  |
| Build                          | PASS: 550 modules; self-contained artifact 4,106,255 bytes                                                                                                                                                      |
| Bundle limitation              | JavaScript 1,115.39 KB / gzip 308.23 KB; unchanged default 500 KB warning                                                                                                                                       |
| Gitleaks                       | PASS: staged source scan, zero findings; installed edit bridge also passes                                                                                                                                      |
| Bandit                         | PASS: unchanged design helpers and current operational helpers via installed edit bridge                                                                                                                        |
| Semgrep                        | PASS: 23 applicable official rules on 50 source/tool targets, zero findings, approximately 100% parsed                                                                                                          |
| Registry/integrity             | Exact Three.js/types verified; official Zod archive SRI matches lock and installed util.js bytes                                                                                                                |
| Dependency advisories          | Official npm bulk endpoint HTTP 200; no advisories for 211 locked package names                                                                                                                                 |
| Fresh-context review           | PASS: frontend fixes, schema/CSP boundary, release generator and operational recovery; independently 38 frontend + 27 schema/intake/content + 3 release + 10 safety checks; native verifier reviewed separately |
| Public Chrome                  | PASS LIVE: 32 layouts at 375/768/1024/1440, 12 journeys, zero errors/failed responses                                                                                                                           |
| Dashboard Chrome               | PASS LIVE: 52 layouts, 17 journeys, zero errors/failed responses                                                                                                                                                |
| CSP/content replay             | PASS LIVE: all 20 routes, zero policy violations/page errors/unexpected requests; prohibited visible labels absent                                                                                              |
| Visual inspection              | Full desktop/mobile home and representative dashboard/page screenshots inspected                                                                                                                                |
| Public HTTP/TLS                | PASS: 14 checks, trusted HTTPS, Cloudflare response, exact artifact SHA, seven headers, redirects, private path/method denials and private-port isolation                                                       |
| Direct-origin TLS              | PASS: trusted HTTPS and current artifact SHA identical                                                                                                                                                          |
| Runtime                        | Healthy bounded nonroot/read-only/capability-dropped container; loopback publishing only                                                                                                                        |
| Archive recovery               | PASS: all six files restored locally with exact hashes                                                                                                                                                          |
| Local/live parity              | PASS: all six release files identical; previous02 drift check passed before promotion                                                                                                                           |
| Existing infrastructure        | 11 gateway files unchanged during promotion; all 22 pre-existing containers retain identity/running/health state; all 11 earlier DNS records unchanged                                                          |
| Actual Git/private protections | PASS: main initialized, private paths ignored and unstaged, zero commits/history, no remote                                                                                                                     |
| Installed pre-commit           | Installed; Gitleaks, Bandit and Semgrep each executed and passed                                                                                                                                                |
| Automatic dispatch boundary    | Installed edit bridge manually executed successfully. Automatic invocation on every edit was not independently demonstrated; no actual commit was created                                                       |

## Acceptance criteria and real flows

**W01–W14: 14/14 met for this frontend scope. H01–H08: 8/8 met for static
publication.** W14/H08 require transparent reporting of gate evidence; the
automatic-dispatch boundary above remains explicit. This is not backend or
production-service acceptance.

Public journeys exercised navigation/deep links/history, industry pointer/arrow
tabs, capability selection, FAQ, plan comparison, articles, required contact
validation/review/edit, onboarding/voice preferences/workspace handoff, mobile
focus/Escape/same-route/resize cleanup, mounted reduced-motion changes,
pause/resume, smooth section navigation and scroll-linked progress/reveals.

Operator journeys exercised agent/voice draft coherence, input validation,
confirmed linked booking, search/filter/empty states, call/contact/appointment
relationships, rescheduling/cancellation, retry idempotency, bounded knowledge
upload/removal, evaluations, integration controls, usage/audit, Viewer restrictions,
keyboard skip/focus, mobile menu and reload reset. State is local and resets on reload.

The first publication replay found a blocked dynamic-code probe. The corrected
schema-runtime facade sets Zod jitless before schemas initialize; no dependency
files were changed. Release03 repeats all browser checks and records zero CSP
violations across every destination. Earlier failed runs remain incident history,
not counted as successful acceptance.

## Configuration and security audit

Real secrets found in scanned source/tooling: **no**. Changeable copy, fixture
records, articles, form choices and motion/3D settings have validated data owners.
Environment settings have one typed boundary and .env.example coverage; deployment
settings are validated before writing files and private access fields are stripped.
No provider URL/model/API version/price is embedded in business source; providers
are disconnected. Regression checks guard configuration and obvious secret patterns.

Fixed route/status identifiers, schema keys, CSS syntax, geometric invariants,
HTTP/container protocol paths and CSP jitless policy remain explicit constants.
Private credentials, settings, memory, manual tooling, snapshots and dossier are
ignored, unstaged and absent from Git history. Recovery credentials are recorded
only in CREDENTIALS.md. Scanner coverage is not a complete security certification.

Latest release/inventory verifiers use Docker GET requests over pinned SSH UNIX
channels and read-only SFTP, with bounded replies/deadlines. No remote shell,
exposed daemon listener or server authentication change is used by these verifiers.
The initial journaled Compose promotion precedes this tooling refactor; future
promotion follows the documented procedure and requires new gates.

Raw evidence lives in ignored .local/browser/ and .local/deployment/: public-
verification.json, headless-verification.json, live-security-verification.json,
server-upgrade.json, live-http-verification.json, live-infrastructure-verification.json,
origin-check.json, release-restore.json, native-release-verification.json, native inventory/DNS snapshots and screenshots.

Forms perform local review; no remote submission, account creation, real calls,
calendar/CRM writes, billing, durable customer storage or production alerting exists.
The role selector is not authentication. Publication on one server establishes no
USA/EU compliance, million-user capacity or observed 99.9% uptime result.
