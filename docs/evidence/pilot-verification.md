# Authenticated core pilot verification

Updated: 2026-10-13 UTC. This is a scrubbed evidence summary derived from the private project dossier.

The current single-business release is backend `20261013-native-redaction-capture-10`
and frontend `20261013-native-frontend-06` on the existing server. The guarded
promotion verified 15/15 backend release files, 15/15 application source modules
against the image, six/six frontend release files and the owned gateway fragment.
The backend reached point-in-time readiness, and the frontend served the exact
reviewed HTML and asserted the served same-origin CSP. Fifty unrelated containers and thirteen unrelated gateway
files were preserved. The current runtime keeps native voice and external
follow-up delivery disabled; calendar and CRM permissions remain independently
enabled. Earlier versions and checks below retain their dated scope.

## Verified behavior

- Actual Google owner sign-in, trusted identity binding, administrator two-step verification, secure host-only session cookie and CSRF rejection passed.
- Two older test-data bookings persist with six once-completed jobs and two captured follow-ups. One owner-only booking was confirmed by direct Google Calendar and Free CRM readback, with exactly one approved Gmail inbox confirmation. The same booking was cancelled after a worker restart; a new calendar job completed once and direct Calendar GET showed cancelled. No second follow-up job or inbox conversation appeared.
- An earlier business02 34,386-byte server backup restored into an isolated clone with thirteen table count/content-hash matches against source before and after; the working database was preserved. The backend10 promotion backup was format/digest checked, not separately restored. The new cancellation job proves fresh worker processing after restart.
- The official MCP Python SDK passed four live HTTPS credential scopes, including business/management reads and read-only write denials. Native ChatGPT/Claude client integration was not exercised.
- Prior authenticated native live Chrome passed twenty-one routes, three widths and four flows with zero JavaScript/CSP errors. Actual logout revoked the session; a copied old cookie returned401.
- Dedicated Retell and Vapi configurations were created and read back successfully, with three business tools and sixty-second native duration limits. No native calls or audio samples have run.

## Current release and single-business completion (2026-10-13)

Before promotion, a host-key-pinned, read-only SFTP snapshot found all twelve
files of the prior backend release, six frontend files and the owned gateway
fragment byte-identical to the local baseline. Local candidate guards checked
the five-service Compose layout: only the approved image references and three
API-only, read-only native configuration mounts changed. Persistent and
security files stayed equal except for the separately hash-approved provider
profile. The backend's complete settings loaded with voice and external mail
disabled, capture transport and no recipients.

The backend deployment helper verified the previous running image and ownership,
old-file parity, approved execution policy and resolved layout before stopping
the owned API/worker. It took a valid PostgreSQL custom-format backup with a
matching saved digest, then activated the reviewed image. Its final report records
`ENGINE_UPGRADE_VERIFIED`, 15/15 release-file parity, 15 matching source modules,
ready health and preservation of 50 unrelated containers. The frontend helper
then validated staged Caddy, Compose and Nginx configuration before activation.
Its report records `AUTHENTICATED_PILOT_PUBLISHED`, six/six release-file parity,
exact owned gateway bytes, 13 unrelated gateway files preserved, the exact
public HTML, a served same-origin CSP assertion and an unauthorized business-state response of 401. These are
point-in-time deployment checks, not an uptime or failover measurement.

An existing owner session opened the live Business engine after both promotions.
The page showed three persisted appointments, three contacts, ten jobs and zero
calls. Its Calls panel displayed the configured 60-second/one-call limit,
disabled voice permission and unverified current free-credit readiness. The
Integrations panel labeled calendar/CRM permissions as configuration rather than
connection proof; voice remained disabled, Vapi read-only and follow-ups in
capture mode. Historical follow-up jobs were explicitly marked as lacking a
recorded delivery mode. The same page navigation retained authenticated records;
Chrome reported zero console errors and two warnings. No native operation yet
exists to verify the owner-visible bound/unknown/reconnect states, so full F08
acceptance remains open.

The final local backend PostgreSQL suite passed 194 tests; the frontend passed
97 tests plus type, lint, formatting, contract, release and build checks. The
backend release matched all 15 current Python modules, 14 frozen data/config
files and the archive digest; the frontend package passed 21 Chromium route/login
checks with zero JavaScript, CSP or external-request errors. The last private
configuration audit examined 207 public files against 35 saved private values:
zero matches, zero staged private files and complete environment-example
coverage. A separate Gitleaks scan of the 207 Git-visible files found zero
findings. Product Bandit, Ruff, Mypy, Python package build and focused cached
Semgrep security rules passed in their recorded scopes. Fresh-context review
accepted the exact backend10/frontend06 implementation and pre-deploy bindings.

The release sequence rejected invalid disabled-delivery/SMTP settings and a
stale provider profile before they reached production. It pinned the dedicated
Vapi assistant's recording, detailed logging and PCAP off, and transcript on;
readback confirmed its reviewed v2 revision. The reviewed Retell agent/LLM
readbacks included one-day storage and an opening AI/recording notice. The
owner-only local transcript redaction requires session and CSRF, an ended
same-tenant call and an idempotent tombstone that prevents late provider events
from restoring text. These are code and configuration checks. No real native
call, audio, voice-originated booking, terminal transcript or listening result
has been observed.

The owner approved a single reviewed use of the SSH deployment helpers, whose
Paramiko command-execution functions retain a documented Bandit B601 medium
finding. Automatic approval permitted the exact guarded execution; no scanner
was disabled or suppressed. The read-only snapshot, deployment reports and
post-promotion hash results are the evidence for this exception's outcome.
Provider artifact deletion and historical backup replay safeguards still
prevent full privacy acceptance. Local redaction does not erase provider copies
or old backups.

## Earlier pilot local gates (recorded for backend03)

| Gate                      | Result                                                                                                                                        |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend                   | 144 tests passed; 23 focused lifecycle/intent checks passed                                                                                   |
| Frontend                  | 78 tests passed                                                                                                                               |
| Types/lint                | Mypy14 modules, Ruff41 files, TypeScript and ESLint passed                                                                                    |
| Build/package             | Python wheel/sdist, frontend build and11 packaging/contract checks passed                                                                     |
| Provider code review      | Fresh intent review02 ready                                                                                                                   |
| Native preparation        | Five safety checks passed; fresh review04 ready                                                                                               |
| Frontend promotion safety | Twelve inventory/recovery checks passed; fresh review08 ready                                                                                 |
| Exact frontend06 artifact | 21 maintained-heading page assertions, login render, HTML/nginx hash binding; zero JavaScript/CSP/external requests                           |
| Immutable image           | Fourteen source modules match local and frozen backend03 manifest                                                                             |
| Secret audit              | 184 public files checked against34 saved private values; no matches; private paths ignored/unstaged and environment example coverage complete |
| Security                  | Bandit0; scoped Semgrep79 applicable Python rules/14 runtime files,0findings/errors; latest edit-hook scans clean                             |
| Dependency advisories     | 87 Python and243 npm dependencies,0known advisories at the recorded check                                                                     |

For business02, normal uninstrumented backend182/182, frontend78/types/lint/build, Mypy14, Ruff, Python wheel/sdist and twelve release/contract checks passed. Connector, deployment, egress and operations reviews accepted their scoped changes. The 199-file/35-known-private-value audit found zero matches and complete environment coverage at that check. The frontend build retains its bundle-size warning. Manual shared-hook invocation is verified; automatic dispatch on every write remains unproven.

## Limits and remaining acceptance

Real voice samples and real-call acceptance remain open. External Calendar/CRM/email have a bounded owner-only receipt; unrestricted customer delivery remains unaccepted. Seven prior public HTTP checks passed: readiness200, unauthorized state/intent401, invalid Retell/Vapi authentication401 and valid-authentication/unregistered-call403. The prior actual public browser passed21 route-specific headings with exact HTML hash and zero JavaScript/CSP/external requests. A registered native assistant and passing envelopes do not prove a real conversation.

A guarded local load run measured40requests across4clients with0errors and approximately24ms p95; a separate populated-data run measured approximately188ms p95. Neither proves a million users or simultaneous calls. Passive health samples report their observed periods and unknown gaps; sustained uptime, zero downtime, off-device backup and physical power-loss durability remain unproven. The broader80-criterion production roadmap remains open.

The earlier aggregate source review accepted its recorded synthetic scope with live voice outstanding. Fresh scoped reviews accepted the current business connector and worker correction. A separate actual HTTPS check confirmed served frontend06 HTML and CSP bytes at its recorded time. Native voice, final operator UI, privacy/release closeout and the broader roadmap are not accepted as complete.
