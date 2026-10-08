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
engine persists through HTTP/PostgreSQL. Other workspace views currently use local
state that resets on reload; they do not send operations to external providers.

## Accessibility and delivery

Verify keyboard/focus behavior, narrow layouts, reduced motion, readable errors
and actual CSP violation events. Exercise the exact built artifact. The existing
bundle-size warning is tracked for route splitting and deferred visual modules.

See [public criteria](../../docs/public-frontend-spec.md),
[operator criteria](../../docs/frontend-spec.md),
[deployment](../../docs/frontend-deployment.md) and
[current evidence](../../docs/evidence/pilot-verification.md).
