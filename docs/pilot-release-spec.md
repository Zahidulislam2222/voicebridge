# Authenticated engine pilot acceptance

This extends the accepted local test-data core. The user authorized authentication,
backend publication on the existing server, free-first capacity/uptime work and
minimal live voice testing. It does not establish million-user capacity or sustained
uptime. Paid execution retains the explicit cost boundary in the global rules.

## Acceptance

- [x] R01 Maintained OIDC authorization-code library validates state, PKCE, nonce,
      signature, issuer, audience and expiry against an isolated test issuer.
- [x] R02 Opaque server-owned sessions support expiry, revocation, secure cookies,
      CSRF and owner/operator/viewer role checks. Unbound identities fail closed.
- [x] R03 Browser login/logout and durable dashboard operations use sessions;
      provider/integration capability keys never enter the published frontend.
- [x] R04 A separate migration upgrades populated core state without losing it;
      cross-tenant denials, backup/restore and configuration/secret checks pass.
- [x] R05 Backend/worker deployment is reproducible with constrained containers,
      private database/network, capture-only deliveries and bounded resource use.
- [x] R06 Existing server inventory and drift checks precede deployment; unrelated
      workloads remain intact and every deployed file matches the local release.
- [x] R07 Public authenticated HTTP/browser operations and worker recovery pass;
      actual issuer binding and applicable administrator MFA are verified.
- [x] R08 Provider contracts, profile bindings, call lifecycle/transcript handling
      and webhook/tool authentication are verified against official specifications.
- [ ] R09 A minimal live voice sample has verified current balances, capped cost,
      rights/disclosure and durable outcomes. Live tests do not substitute for local tests.
- [x] R10 Guarded free load testing and persistent health observation report actual
      samples, limits and gaps. Capacity and uptime claims require measured evidence.
- [x] R11 Tests, types, lint, security, dependency, package/container and frontend
      build gates pass; a fresh context reviews the final change against this spec.
- [x] R12 Dossier, credentials, recovery checkpoint and evidence reflect before/after,
      ongoing actions, unknown results and the next authorized action.

## Configuration inventory and research

OIDC discovery, client credentials, redirect URI, scope, accepted signing algorithms,
cookie names, session/login expiry, cookie security, trusted origins and identity
bindings belong to typed settings and maintained validated access data. OAuth
credentials and server secrets stay private. Protocol fields remain in the protocol
module. The Calendar installed-app client is not a web login client.

Deployment stage/bind address, internal service names, resource limits, image pins,
paths, API origins, gateway routes and observation thresholds belong to deployment
configuration. The existing static release stays auditable until replacement passes.

References consulted before implementation:

- https://developers.google.com/identity/openid-connect/openid-connect
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://docs.authlib.org/en/v1.7.0/oauth2/client/web/starlette.html

Google web credentials must be configured in the already-selected Portfolio Hub
project. No extra cloud project, billing activation or paid resource is needed for
this preparation. All criteria start open; close only with actual evidence.

Frontend revisions must preserve prior drift snapshots in separate per-release directories and refuse an existing candidate snapshot rather than overwrite recovery evidence.

Frontend promotion requires the exact six-file baseline/candidate inventory, the original gateway main bytes saved before mutations, route-specific content assertions and HTML/nginx/CSP-bound proof. Gateway inventory membership and unrelated bytes are rechecked before activation, after publication and during rollback.

Gateway candidate/rollback staging is created exclusively, refuses an existing file/symlink, tracks ownership immediately, and verifies pending bytes again immediately before promotion.

R01–R08/R10 accepted only for the recorded test-data-business authenticated pilot. External delivery is disabled; guarded capacity and observation report measured scope. R11 final aggregate review approves the verified free pilot scope, and R12 records are synchronized. R09 real voice remains open. Eleven of twelve pilot criteria are accepted; this count is not a project completion percentage. See docs/evidence/pilot-verification.md.
