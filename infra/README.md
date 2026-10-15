# Integration infrastructure

`n8n/confirmation.workflow.json` maintains the development confirmation workflow
and receipt/operation contract. Configure credentials and identity privately;
inspect existing imports before creating or publishing a workflow. Never embed
keys in workflow exports.

The current authenticated release has independently enabled owner Calendar and
CRM permissions with one bounded booking/readback and Gmail owner receipt. The
earlier owner-only Retell call never joined media and later ended. Creation is
disabled; a separate owner-only GET path supports exact bound-call recovery;
external follow-ups remain off and use capture mode. The n8n workflow file is
source configuration; publishing it
does not import or activate a workflow or create cloud resources. Review real
destinations, consent, provider quotas, security and deletion before broader
activation. See [operations](../docs/core-engine-operations.md),
[API](../docs/api/README.md) and [roadmap](../docs/roadmap.md).

The current export release and configuration boundaries are documented in
[release evidence](../docs/evidence/tenant-export-release-20261015.md),
[configuration](../docs/configuration.md), [providers](../docs/integrations.md)
and [monitoring](../docs/monitoring.md). Future infrastructure changes require
staged capacity, security, cost and recovery acceptance before activation.
