# Integration infrastructure

`n8n/confirmation.workflow.json` maintains the development confirmation workflow
and receipt/operation contract. Configure credentials and identity privately;
inspect existing imports before creating or publishing a workflow. Never embed
keys in workflow exports.

The current authenticated release has independently enabled owner Calendar and
CRM permissions with one bounded booking/readback and Gmail owner receipt. The
owner-only native route registered one Retell web call without media; its
one-call slot remains occupied pending reconciliation;
external follow-ups remain off and use capture mode. The n8n workflow file is
source configuration; publishing it
does not import or activate a workflow or create cloud resources. Review real
destinations, consent, provider quotas, security and deletion before broader
activation. See [operations](../docs/core-engine-operations.md),
[API](../docs/api/README.md) and [roadmap](../docs/roadmap.md).
