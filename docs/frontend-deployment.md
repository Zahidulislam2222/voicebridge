# Frontend publication and pilot handoff

**Live:** https://voicebridge.zahidul-islam.com/ — current frontend
`20261008-frontend-06`, paired with authenticated backend `20261008-pilot-03`.
Six frontend and twelve backend files match local/live. Latest native public browser
passes21maintained page-heading assertions and login render with zero JS/CSP errors.
Dedicated native provider profiles are configured; real voice calls remain untested.
See [current pilot evidence](evidence/pilot-verification.md).

The sections below retain the historical static release03 publication evidence.
Current pilot CSP permits same-origin engine connections. Other remote connections,
frames, workers and form submissions remain excluded by the verified policy.
No new paid resource or Kubernetes cluster was provisioned.

## Historical static release and evidence

Six immutable files: html/index.html, nginx.conf, compose.yaml, site.caddy,
SHA256SUMS and release.json. Exact inline script/style CSP hashes prohibit remote
connections, frames, workers and form submission. Zod initializes in jitless mode.
The container runs nonroot/read-only, drops capabilities, disallows privilege gains,
publishes only to a loopback port and has bounded CPU/memory/PIDs/logs plus health/restart.

All six files match local/live SHA-256 and restored archive hashes. Previous02
was downloaded into the ignored live snapshot and matched local before promotion.
All eleven gateway files stayed unchanged; the existing twenty-two containers
retain identity/running/health state. Native Cloudflare inventory confirms all
eleven previous records unchanged; only the reserved project hostname was added.

Compose/Nginx and gateway validation pass. Trusted direct-origin and public HTTPS
serve the exact local artifact; the public response passes fourteen HTTP/security
checks. Sandboxed Chrome passes 32 public layouts/12 journeys, 52 operator layouts/
17 journeys and all20-route CSP checks. See [full evidence](evidence/frontend-verification.md).

## Local-first update procedure

Deployment settings have one validated boundary in tools/prepare-frontend-release.mjs;
private access fields are stripped. Maintained templates live in deploy/.
Private operational settings and helpers live in ignored .local/deployment/.

1. Inventory current native DNS, Docker, listeners and available capacity; preserve
   other project ownership. Read and minimally update the existing shared registry.
2. Download live release/site files into ignored _live_server/ and compare every
   touched file with local. Reconcile newer live changes before implementation.
3. Implement locally, run source/security/build/real-flow gates and independent review.
4. Choose a fresh release ID; generation refuses to overwrite an existing release.
   Run npm run presentation, npm run test:presentation, npm run test:release and
   node tools/prepare-frontend-release.mjs .local/deployment/settings.json.
5. Archive and restore locally, then verify all hashes. Upload immutable files through
   the existing deploy account; use pinned-host administrative access for this project.
6. Validate Compose/Nginx through the documented administrative CLI, start only
   the VoiceBridge Compose project, verify health,
   hardening, bindings, release parity and gateway preservation. Advance the current
   pointer only after checks pass; failure restores previous service and pointer.
7. A changed project gateway must be staged outside the imported wildcard, validated
   as a candidate before atomic activation, then validated/reloaded with rollback.
   DNS mutations use explicit record-name/type/address guards that survive python -O.
8. Repeat trusted/public HTTPS, security/header/private-path/port, real UI and final
   local/live hash checks. Update dossier first, then public evidence, ownership and recovery.

## Backup and rollback

Release03 off-server archive: 2,415,923 bytes; SHA-256
`2b32e1e060f9a1f17791201b0dd5b9a6e75de86b301b7aebdc07258132afcbe5`.
All six restored file hashes match. Keep releases01/02 and their archives.
This proves static-release restoration, not customer-data recovery.

For rollback, start retained release02 under the same unique Compose project,
restore its current pointer, verify health/HTTPS/hash parity, and record the rollback.
The gateway fragment is identical between02/03, so that rollback requires no shared
config change. For a gateway change, restore only the project fragment, validate and
reload; preserve every unrelated file and another writer's changes. For removal,
remove only the owned site/container/DNS record using saved before-state. Never prune
shared Docker resources, delete unrelated volumes, or replace the shared gateway main file.

## Reusable acceptance verifier

The latest local upgrade_server.py is a post-upgrade verifier. It cannot mutate
Docker or execute a remote shell; it reads the native Docker API through a pinned
SSH UNIX-socket channel and reads files through SFTP. It verifies approved image,
exact release mounts, health/security/resource/log settings, active gateway site,
current pointer and all six release hashes. Live execution passes. Native transport
responses/deadlines are bounded; project-local AsyncSSH is registry-pinned. Native
inventory similarly confirms the other containers. Future promotions use the
procedure above and need new drift/gate/review evidence; no new API mutation path
is presented as tested automation.

## Recovery and boundaries

Access and exact infrastructure details are in the gitignored CREDENTIALS.md and
shared infrastructure registry. Raw before/after inventories, host-pinned SSH
results, restore/parity and browser evidence are kept in ignored project folders.
Actual Git protections pass; Windows pre-commit is installed and all three scanners
have been exercised. Manual edit-bridge success does not prove every-edit dispatch.

The earlier static release had no backend/authentication/provider execution.
The current release adds the persistent Business engine console and Google owner
sessions; the twelve other workspace views keep local state. Native voice and
external business delivery remain separate integration gates, and public intake
forms still perform local review without remote submission.
This existing server is one failure domain; legal compliance, million-user capacity,
production monitoring and 99.9% uptime remain separately gated roadmap work.
