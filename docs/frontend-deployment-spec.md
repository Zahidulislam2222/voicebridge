# VoiceBridge frontend publication criteria

User requested infrastructure inspection and a project subdomain on 2026-10-07.
This extends local frontend delivery to preparing publication on the existing
shared VPS. No new paid resource, subscription or Kubernetes cluster is required.

1. H01: Inspect shared infrastructure instructions, platform-native DNS inventory,
   server listeners/capacity and native Docker inventory before allocation.
2. H02: Reserve only voicebridge.zahidul-islam.com and an actually unused loopback
   port in the required shared ownership registry; coordinate existing apps.
3. H03: Local frontend gates and fresh review pass; no real provider/backend
   credentials, accounts, customer data or outbound messaging are introduced.
4. H04: Build a versioned static release with environment-owned deployment
   settings, bounded nonroot/read-only container and project-only Caddy site.
5. H05: Restore an off-server release archive locally and verify every SHA-256.
6. H06: Deploy locally verified files, validate Caddy, configure only the intended
   DNS record, and verify direct-origin/public HTTPS plus real public browser flows.
   A failed startup or post-start acceptance check restores the previous service
   and release pointer; the pointer advances only after acceptance checks pass.
7. H07: Prove local/live hashes for every release/site file and preserve existing
   applications, shared gateway main file and portfolio DNS.
8. H08: Record release, ownership, recovery, rollback and actual credential/private
   Git/hook gate evidence. Missing access/gates remain explicit.

Current scope boundary: static frontend only. The existing server is one failure
domain. No legal-compliance, authentication, million-user or uptime claim follows
from publication. Frontend forms perform local review and no remote submission.

Acceptance: **H01–H08, 8/8 met for static publication**. Release03 is live and
verified; all six file hashes match local/live/restored archive. Native inventory,
ownership reservation, container/gateway/DNS/HTTPS checks and real live browser
flows are recorded in evidence/frontend-verification.md. Actual Git private
protections and installed pre-commit scanners are verified. Manual edit-bridge
execution passes; automatic invocation on every edit is not independently proven.
No real provider/backend/customer-data or new paid infrastructure was introduced.
