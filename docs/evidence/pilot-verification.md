# Authenticated core pilot verification

Updated: 2026-10-07T23:21:05.180581+00:00 UTC. This is a scrubbed evidence summary derived from the private project dossier.

The current live authenticated pilot is backend03/frontend06. All twelve backend and six frontend files match local/live; fourteen runtime modules match the frozen image. Two preflight format mismatches stopped safely before live process changes; actual platform output was then verified and the reviewed reconciliation succeeded. Backend promotion preserved twenty-seven unrelated/database/capture containers; frontend promotion preserved ten unrelated gateway files.

## Verified behavior

- Actual Google owner sign-in, trusted identity binding, administrator two-step verification, secure host-only session cookie and CSRF rejection passed.
- Two test-data bookings persist across page reload and worker restart. Six calendar/CRM/follow-up jobs completed once, with two captured follow-ups. External calendar/CRM delivery and external email remain disabled.
- A server database backup restored into an isolated clone with thirteen table count/hash matches; the working database was preserved.
- Prior authenticated native live Chrome passed twenty-one routes, three widths and four flows with zero JavaScript/CSP errors. Actual logout revoked the session; a copied old cookie returned401.
- Dedicated Retell and Vapi configurations were created and read back successfully, with three business tools and sixty-second native duration limits. No native calls or audio samples have run.

## Current local gates

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

The frontend build retains its bundle-size warning. Manual shared-hook invocation is verified; automatic dispatch on every write remains unproven. Static reviews establish code findings, while runtime results are recorded separately.

## Limits and remaining acceptance

Real voice samples, external business-provider delivery and real-call acceptance remain open. Seven current public HTTP checks pass: readiness200, unauthorized state/intent401, invalid Retell/Vapi authentication401 and valid-authentication/unregistered-call403. Current actual public browser also passes21route-specific headings with exact HTML hash and zero JavaScript/CSP/external requests. Read-only database/health inspection confirms one identity binding, six completed jobs, no pending jobs/sessions, two captures and101health samples/100successful/one unsuccessful with0unknown seconds at this check. A registered native assistant and passing envelopes do not prove a real conversation.

A guarded local load run measured40requests across4clients with0errors and approximately24ms p95; a separate populated-data run measured approximately188ms p95. Neither proves a million users or simultaneous calls. Passive health samples report their observed periods and unknown gaps; sustained uptime, zero downtime, off-device backup and physical power-loss durability remain unproven. The broader80-criterion production roadmap remains open.

Final aggregate source review: READY FOR VERIFIED FREE PILOT SCOPE WITH LIVEVOICE OUTSTANDING. The review independently ran no tests/deployment. A separate actual HTTPS check confirms served HTML bytes and the exact live CSP header match the local frontend06 package. The whole project and real voice are not accepted as complete.
