# VoiceBridge frontend

React, TypeScript and Vite provide the public website and operator workspace.
Three.js renders voice artwork; Motion handles transitions and scroll effects.
Fonts and artwork are served locally. The Business engine console uses generated
OpenAPI types and supports server-session authentication.

Run from the repository root:

```sh
npm ci
npm run dev
npm test
npm run typecheck
npm run lint
npm run format:check
npm run build
```

`npm run presentation` produces the self-contained browser artifact used by release
tooling. `npm run test:presentation`, `npm run test:release` and
`npm run test:core-contracts` validate packaging and client-contract drift.

## Configuration and state

`src/config/settings.ts` is the typed browser configuration boundary;
`config/development.json` owns server defaults. Maintained copy and interface
records belong to validated data files. Never place secrets in `VITE_` variables:
they are included in browser bundles.

Set `VITE_CORE_API_URL` and matching backend origins to connect the console.
Use `VITE_CORE_SESSION_AUTH=true` in a session-authenticated release. The Business
engine persists through HTTP/PostgreSQL. Native call controls are bounded by the
server's provider and owner authorization gates. A Retell web call was
registered without media and currently holds the one-call slot; real audio acceptance remains
open. Other workspace views
currently use local state that resets on reload; they do not send operations to
external providers.

## Accessibility and delivery

Verify keyboard/focus behavior, narrow layouts, reduced motion, readable errors
and actual CSP violation events. Exercise the exact built artifact. The existing
bundle-size warning is tracked for route splitting and deferred visual modules.

The deployed release matched seven frontend files to the server after local
97-test and packaged browser checks. It serves the artwork separately and
compresses eligible HTML. A fresh Google owner sign-in and Calls-panel readback passed. The panel
shows both male providers and bounded call controls. These
checks do not establish live voice calls or future-scale reliability. See
[current release evidence](../../docs/evidence/owner-release-20261013.md),
[public criteria](../../docs/public-frontend-spec.md),
[operator criteria](../../docs/frontend-spec.md),
[deployment](../../docs/frontend-deployment.md) and
[earlier evidence](../../docs/evidence/pilot-verification.md).
