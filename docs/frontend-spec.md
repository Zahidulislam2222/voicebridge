# Frontend implementation acceptance criteria

Written before feature implementation on 2026-10-07. This slice implements the
local-interaction frontend from Phase 2; it does not close backend/provider, production,
legal, capacity, or uptime criteria.

1. F01: Showcase has a distinct visual identity, generated artwork and a working workspace CTA; developer documentation records the local-interaction boundary.
2. F02: Twelve operator destinations support deep links, back navigation and a usable mobile menu.
3. F03: Overview metrics derive from maintained fixture records and expose recent calls and appointments.
4. F04: Agent draft editing validates required fields, preserves drafts during navigation and does not imply provider publishing.
5. F05: Voice selection updates the agent draft; voice testing is a local visual interaction with no microphone or paid call.
6. F06: Confirming a controlled call creates a linked call, appointment, contact and automation record once; replay cannot duplicate the booking.
7. F07: Call search, outcome filters, detail transcripts and empty states work.
8. F08: Appointments can be rescheduled or cancelled after explicit confirmation; cancellation does not imply an external provider operation.
9. F09: Contacts can be searched and inspected with linked call history.
10. F10: Automation failure detail and retry work; retry is idempotent and retains the original appointment.
11. F11: Knowledge accepts only bounded UTF-8 plain text/Markdown, renders text safely and supports search/removal.
12. F12: Evaluations show maintained fixture scenarios and local execution results.
13. F13: Integrations disclose disconnected real providers, exercise local connection state, and never accept or expose credentials.
14. F14: Usage and audit screens derive local usage and events without claiming billing or real monitoring.
15. F15: Viewer role prevents all mutations through the local service boundary, not just disabled buttons.
16. F16: Forms, navigation and dialogs are keyboard usable; visible focus, modal focus return, reduced motion and 375/768/1024/1440px layouts are checked.
17. F17: Product copy/local fixtures belong to validated data files; settings have one typed boundary; source secret/config regression checks and tests/types/lint/security/build/review results are reported.

## Configuration inventory

| Variable family                                                                                             | Owner                                                                                                              |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Branding, labels, agent greeting, sample scenario, voice profiles, integration catalogue, test-data records | apps/web/src/data/content.json and validated workspace data, validated at bootstrap                                |
| local delays, upload/input limits, default role, timezone, locale, animation duration                       | apps/web/src/config/settings.ts with safe public environment overrides                                             |
| Frontend port/host                                                                                          | config/development.json through tools/development-settings.mjs; VITE_DEV_HOST and VITE_DEV_PORT                    |
| Image reference                                                                                             | apps/web/public/voice-sculpture.png; asset provenance in docs/design                                               |
| Design colors/type/spacing                                                                                  | apps/web/src/styles.css semantic design tokens; locally served licensed WOFF2 fonts                                |
| Provider secrets and endpoints                                                                              | No real providers in this slice; future backend settings only                                                      |
| Persistence                                                                                                 | In-memory local state, reset on reload; no secret/customer browser storage                                         |
| Preview dependencies                                                                                        | Exact registry versions and package-lock.json; presentation tooling embeds all runtime assets with no CDN requests |

## Gates and evidence boundary

Automated workspace-service tests exercise confirmations, linked records, role denial,
retry idempotency, cancellation and validation. Browser checks exercise the actual
UI and responsive layouts. Missing tools/gates stay recorded as missing. The latest real Git/private protections and installed scanners pass; automatic
edit dispatch remains explicitly unverified. Latest frontend/browser acceptance
and scope are recorded in evidence/frontend-verification.md.

Visible-copy requirements were amended by the user after the initial slice: use
product names, retain honest integration limits in developer documents and follow
W09 for visible labels. Latest operator replay passes 52 layouts/17 journeys.
