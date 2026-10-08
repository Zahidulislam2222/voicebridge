# Frontend developer handoff

This handoff records the earlier static public/operator release. Current Business
engine integration, authentication and deployment evidence are in
[pilot verification](evidence/pilot-verification.md) and [frontend README](../apps/web/README.md).
Counts and disconnected-provider statements below describe the earlier release.

VoiceBridge now has a complete public page map and the approved operator dashboard.
The frontend is live at https://voicebridge.zahidul-islam.com/ and passes its
public/operator/browser gates. Read [verification evidence](evidence/frontend-verification.md)
for the frontend-only acceptance boundary.

## Page map and behavior

| Public route  | Content and interactions                                                                                                 |
| ------------- | ------------------------------------------------------------------------------------------------------------------------ |
| #/welcome     | Full homepage, controllable 3D sculpture, product panel, workflow, features, industry tabs, integrations, FAQ and footer |
| #/features    | Product view and full capabilities/workflow                                                                              |
| #/solutions   | Industry selectors and business conversation workflow                                                                    |
| #/pricing     | Three plan descriptions and detailed comparison; pricing by enquiry                                                      |
| #/company     | Company story and principles                                                                                             |
| #/resources   | Articles, with deep links #/resources/article-id and browser history                                                     |
| #/contact     | Required-input validation, local review and edit                                                                         |
| #/get-started | Business/voice preferences, review and workspace handoff                                                                 |

The twelve dashboard destinations remain Overview, Agents, Calls, Appointments,
Contacts, Knowledge, Automations, Evaluations, Integrations, Usage, Audit and Settings.
Existing linked booking, draft, knowledge, retry and permission flows remain in-memory.
Reload resets workspace state. Contact/onboarding perform local review and never
claim remote submission or account creation. No backend/provider execution is connected.

## Source owners

| Concern                                                              | Owner                                                                                  |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Maintained public copy, articles, choices and visual/motion settings | apps/web/src/data/site.json with site.ts validation                                    |
| Operator copy and fixture records                                    | data/content.json, validated workspace data and contracts.ts                           |
| Public page structure and responsive styling                         | components/showcase.tsx and public-site.css                                            |
| Animated WebGL resource lifecycle/static fallback                    | components/voice-sculpture.tsx                                                         |
| Strict-CSP schema initialization                                     | config/schema-runtime.ts sets jitless before every browser schema                      |
| Live reduced-motion preference                                       | utils/motion-preference.ts, consumed by all animated components                        |
| Local intake normalization and validation                            | services/intake.ts                                                                     |
| Operator state/actions/permissions                                   | workspace.tsx and services/                                                            |
| Public environment settings                                          | config/settings.ts; .env.example                                                       |
| Local host/port                                                      | tools/development-settings.mjs; config/development.json                                |
| Portable packaging/artwork                                           | tools/create-presentation-preview.mjs, presentation-protocol.mjs and config/artwork.ts |
| Static publication boundary and templates                            | tools/prepare-frontend-release.mjs; deploy/                                            |

Secrets never belong in VITE_ settings or browser data. Replace the local service
with authenticated organization-scoped API operations in Phase 3. The browser role
selector provides presentation behavior, not a server security boundary. Retain
booking confirmation, idempotency, relationships and permission tests as contracts.

## Verification and next checks

The earlier static release passed 70 application tests, three packaging checks, three release
checks, types, ESLint, formatting, security scans and build. Independent source/
publication reviews pass. Live public Chrome: 32 layouts/12 journeys; dashboard:
52 layouts/17 journeys; all20-route CSP replay records zero violations/errors.

```sh
npm test
npm run typecheck
npm run lint
npm run format:check
npm run presentation
npm run test:presentation
npm run test:release
```

Preserve ignored personal replays in manual-tests/. Run public_frontend_browser_test.mjs
and frontend_browser_test.mjs in a browser-enabled Windows session. They launch only
their own fresh sandboxed Chrome and preserve user tabs. Evidence is written under
.local/browser/. The updated public replay covers mounted preference changes,
pause/resume, smooth navigation and scroll reveals.

JavaScript is 1,115.39 KB / 308.23 KB gzip; the default 500 KB warning remains. Route/
renderer code splitting is a future hosted-delivery optimization. The portable
artifact intentionally embeds its required assets for local delivery.

Actual Git private ignore/staging/history protections are verified; Windows
pre-commit is installed and its Gitleaks/Bandit/Semgrep commands pass. Installed
edit-bridge manual execution passes; automatic dispatch on every edit is not
independently demonstrated. These results do not establish legal compliance,
capacity, complete security or uptime. Live parity, promotion and rollback are in
[frontend-deployment.md](frontend-deployment.md).

## Assets

Three.js generates the hero sculpture in code; the inspected optical-glass PNG
supports the workflow and operator view. Existing image generation exposed no model
version/cost, so neither is asserted. DM Sans and Manrope are self-hosted and retain
SIL Open Font Licenses. The presentation embeds the fonts and artwork. Visual
references informed an original direction; no paid gallery prompt was copied.
