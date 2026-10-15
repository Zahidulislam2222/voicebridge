# Owner recovery release — 2026-10-15

Historical recovery16 evidence. The [later audit18 release](mcp-denial-release-20261015.md) is current.

Backend `20261015-native-reconciliation-16` and frontend
`20261015-native-reconciliation-09` were deployed to the existing server after
local verification and fresh live drift checks. All **16 backend and seven
frontend release files** match local hashes; all 15 backend source modules match
the frozen image. The promotions preserved 57 neighboring containers and 13
unrelated gateway files. A 36,773-byte PostgreSQL backup passed format/digest
checks; that particular backup has not been independently restored.

Call creation and external mail are disabled. Follow-ups use capture with no
recipients. A separate default-false `VB_NATIVE_RECONCILIATION_ENABLED` setting
permits owner-only, CSRF-protected GET-based recovery of an exactly bound call.
Provider call ID, agent ID, operation metadata and terminal status must match;
UNKNOWN creation without a returned ID remains manual. Recovery clears the
encrypted media grant, records one terminal transition and copies no transcript
or media credential. Vapi metadata is read from its documented
`assistantOverrides.metadata` location.

## Verification

| Gate | Recorded result |
| --- | --- |
| Backend | Full suite 218/218 passed in 170.20 seconds; after the final type-only annotation, recovery/configuration/contract/load checks 21/21 passed |
| Frontend | 97 tests; TypeScript, ESLint, formatting, production build and contract/release checks passed |
| Types/lint/packages | Mypy 15 runtime files, CI-scoped Ruff, Python wheel/sdist passed |
| Security | Runtime Bandit and Semgrep passed; 79 Semgrep rules across 15 files found zero findings/errors; visible-source and 14-commit history Gitleaks found zero secrets; installed edit hook passed |
| Configuration | 214 public files checked against 37 saved private values: zero matches/private staging, complete environment example coverage |
| Dependencies | 86 locked Python dependencies and npm audit reported zero known advisories at this check; no dependency was added |
| Independent review | Approved final code and exact candidate16 controls; independently passed 18 recovery and 54 deployment guard tests |
| Browser | 21 packaged routes and 21 actual public routes passed, with zero JavaScript/CSP/external-request errors; seven intercepted recovery journeys passed |
| Actual owner HTTP | Session/read status 200; existing Retell reconciliation 200 with actual ledger retirement audited at `2026-10-14T23:09:30.854826Z`; disabled create 403 `external_execution_disabled`; no new calls or operations |
| Actual owner UI | Retell DONE, creation controls absent, no overflow and zero fresh-page console errors; two warnings |
| Durable state | Three appointments, three contacts, one historical call and ten jobs remained unchanged |

The owner UI already displayed DONE because its call had ended; the new reconciliation audit verifies that the separate bound operation ledger was retired after provider verification.

The load safety guard initially stopped after 12 requests at 67.48% host CPU,
with zero HTTP errors. Its unchanged 65% threshold was preserved. A quiet rerun
completed 40 requests at four-client concurrency with zero errors and 151 ms
p95; the subsequent quiet full suite passed. This is a bounded measurement.

The review corrected recovery being unavailable when creation was disabled and
the Vapi metadata nesting before deployment. A final type inference correction
used a distinct immutable candidate; the unused earlier candidate was preserved.
The release-template test now accepts Windows CRLF without changing runtime
templates. Frontend bundle-size and Docker build ARG-default warnings remain;
the broader helper-only Ruff S603 findings are outside the configured CI scope.

## Remaining acceptance

[Recovery criteria N01–N06](../native-reconciliation-spec.md) are accepted for
this owner recovery release. At this milestone **24/50 implementation and 0/30 readiness criteria**
are accepted in the [original roadmap audit](roadmap-status-20261015.md).
This milestone did not close the other56 requirements; the later audit release accepts one additional original criterion.

The twelve presentation/operator destinations still use controlled local state;
`#/engine` is the authenticated persistent console. Real Retell/Vapi audio,
human listening and voice-originated booking remain unverified; listening was
deferred by the owner. Native assistant-client MCP, denial auditing, n8n crash
recovery, provider/backup deletion, launch legal review, monitored reliability
and measured scale retain their gates. No new native call, external message,
billing change, cloud resource or Google Doc/PDF update occurred in this task.

Earlier [owner release](owner-release-20261013.md) and
[release evidence](pilot-verification.md) retain their dated scopes. Sustained
uptime, zero downtime, million-scale capacity and customer readiness are not
established by these deployment checks.
