# Owner voice release evidence — 2026-10-25

Backend `20261025-video-voice-20` replaced backend `20261015-tenant-exports-19`
on the existing server on 2026-10-25 between 05:16 and 05:20 UTC. Frontend
`20261015-tenant-exports-10` was unchanged; a read-only check matched its seven
live files to the local release. This record supersedes the current-state lines of the
[October 15 release evidence](tenant-export-release-20261015.md), which remains
the dated record for that release. Releases 21 to 23 and the first booked owner
call are recorded in the [owner voice calls evidence](voice-calls-20261025.md).

## Before and after

| Area                        | Before (backend 19, 2026-10-15)                         | After (backend 20, 2026-10-25)                                                       |
| --------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Owner call creation route   | Disabled by the execution policy                        | Enabled for the owner session; still gated by a fresh free-credit receipt            |
| Free-credit receipt         | 15-minute validity                                      | Up to 2 hours, bounded at 7200 seconds in typed settings                             |
| Current receipt             | Expired October 13 receipt                              | Same expired receipt, so every create is refused before any provider request         |
| Maximum call length         | 60 seconds (typed maximum 60)                           | 180 seconds for the owner route (typed maximum 180, default still 60)                |
| Retell agent                | Version 0, 60-second limit                              | Version 1, 180-second limit; prompt states calendar/CRM booking and no email; v0 kept |
| Approved provider snapshot  | October 13 readback                                     | Fresh version 1 readback including two provider-added LLM fields                      |
| Vapi                        | Not attempted                                           | Not attempted; its receipt stays unverified and its template keeps 60 seconds        |
| Read-only call recovery     | Enabled                                                 | Enabled                                                                              |
| External email              | Disabled; capture only; no recipients                   | Unchanged                                                                            |
| Calendar and CRM permission | Enabled for owner bookings                              | Unchanged                                                                            |
| Backend tests               | 252 passed                                              | 254 passed (two new bound cases) plus a new 180-second preflight/override test       |
| Live file parity            | 16/16 backend, 7/7 frontend                             | 16/16 backend, 15/15 image source modules, 7/7 frontend                              |
| Neighbouring services       | 57 unrelated containers preserved                       | 77 unrelated containers preserved; gateway unchanged                                 |

## What changed and why

The October 13 owner call ended with `error user not joined` because it was
created by a direct technical request and no browser joined its media grant
before the provider timeout. The create, bind and browser join path was already
implemented. The 60-second ceiling was too short for a booking that collects name,
phone, email, service and time with confirmation, so the typed maximum is now 180
seconds and the Retell agent was republished at that limit.

A fresh provider readback showed that Retell now returns two additional LLM fields.
The pre-call safety check compares the live agent and LLM with an approved snapshot
exactly, so the release carries a fresh snapshot. Without it, every create would have
failed with `native_profile_drift` even with the route enabled.

The deployment guard accepts voice creation together with read-only recovery only
with an explicit voice approval, and accepts native limit changes only when the
values equal an approval bounded by the typed settings maximums.

## Verification

| Gate                  | Result                                                                                       |
| --------------------- | -------------------------------------------------------------------------------------------- |
| Backend full suite    | 254/254 passed on PostgreSQL                                                                 |
| Focused native/guards | Native, settings and recovery tests plus deployment guard suites: 119 passed                 |
| Static checks         | Mypy 15 files, Ruff check, Bandit medium+ and Gitleaks history/changed files clean           |
| Commit hooks          | Gitleaks staged, Bandit and Semgrep passed                                                    |
| Image identity        | 15/15 application modules in the image equal the reviewed source                              |
| Fresh-context review  | Approved with notes; line-ending, duplicate-limit and test-coverage notes fixed before release |
| Deployment            | Drift check, database backup (36,354 bytes, digest recorded), guarded rollout, readiness ready |
| Frontend              | Read-only live parity 7/7 against frontend release 10                                         |

## Limits

No live call was made in this release and no audio, conversation, tool call or
voice-originated booking has been observed. Calls stay refused until the owner
performs a current billing check and a new immutable release carries that receipt.
P09 in the [provider specification](../provider-interoperability-spec.md) stays open
until a real call joins audio, runs a business tool and books. The original roadmap
stays at 26/50 implementation and 0/30 readiness criteria. One-million-scale and
99%/99.9% uptime remain future objectives described in the
[capacity roadmap](../capacity/scaling-roadmap.md) and [reliability plan](../reliability.md).

Note on pacing: the agent ends a call after 10 seconds of silence, Retell business
tools have a 10-second timeout, and only one owner call can run at a time.
