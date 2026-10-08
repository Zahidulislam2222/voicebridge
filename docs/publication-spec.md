# Public repository acceptance criteria

This publication includes the maintained frontend, backend, migration history,
validated configuration/data, integration contracts and reproducible build tools.
It changes documentation and repository metadata; it does not change deployed code.

1. PUB01: GitHub owner and commit author match the verified project owner.
2. PUB02: Credentials, environment files, private records, machine instructions,
   browser captures and document exports are ignored and absent from publication.
3. PUB03: Source and staged content pass secret/configuration audits and security
   scans without bypassing installed hooks or suppressing findings.
4. PUB04: Root/frontend/backend READMEs and a navigable documentation index explain
   installation, configuration, architecture, API, deployment and operations.
5. PUB05: Public documents include jurisdiction applicability, privacy, consent,
   voice rights, retention, threat model, incident response and release gates.
6. PUB06: The roadmap specifies separate account/session/call workloads, a future
   one-million-plus concurrent-user topology, capacity evidence and provider quotas.
7. PUB07: Reliability defines 99% and 99.9% objectives, measurement windows, error
   budgets, observability, redundancy, backup/restore and rollout procedures.
8. PUB08: Tests, types, lint, security and build gates run locally; public CI uses
   standard runners, no paid API calls, and no uploaded private artifacts.
9. PUB09: Public changes receive a fresh-context review and findings are resolved.
10. PUB10: An ordinary push is verified against the remote commit/tree/author;
    repository description, topics, security reporting and workflow results are checked.
11. PUB11: After publication, the existing Google Doc is identified and read fully;
    targeted updates preserve prior content, document identity and native structure.
12. PUB12: The refreshed PDF is exported from that same Doc, validated before
    canonical replacement, and stored under this project's my-project-view/.

If no matching existing Google Doc can be found, PUB11/PUB12 remain unresolved;
publication does not authorize creating a replacement document.
