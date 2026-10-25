# Owner voice calls evidence — 2026-10-25

Backend `20261025-video-call-23` is live. Three guarded releases followed backend
`20261025-video-voice-20` on 2026-10-25 so the owner could make five bounded Retell
web calls. Frontend `20261015-tenant-exports-10` was unchanged. This record supersedes
the current-state lines of the [backend 20 evidence](voice-release-20261025.md),
which remains the dated record for that release.

The caller in every call was a synthetic test voice played through speakers into the
browser microphone. The Retell agent, the FastAPI engine and worker, PostgreSQL,
Google Calendar and the HubSpot CRM record were all live. No phone number was used:
these were browser web calls.

## Releases

| Release | Started (UTC) | Change from the previous release                                                                                                                | Result                                                                                |
| ------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 21      | 05:50         | Fresh Retell free-credit receipt (USD 10.00 balance, no payment method, auto-recharge off); Vapi receipt omitted so Vapi stays refused          | 16/16 files, 15/15 source modules, 77 unrelated containers preserved, readiness ready |
| 22      | 06:27         | Service names matched without regard to case or spacing (`canonical_service()`); new image, same receipt                                        | Same parity checks; fresh-context review approved with notes                          |
| 23      | 07:03         | Rotated Google Calendar refresh token, accepted only through a new explicit token-rotation approval in the guarded deployment; same image as 22 | Same parity checks; readiness ready                                                   |

Each release took a database backup first and kept the previous release as its
rollback target. No provider call was made by any deployment.

## Calls

| Call | Time (UTC) | Outcome                                                   | Cause                                                                                                                          | Correction                                        |
| ---- | ---------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| 1    | 06:07      | Audio joined and the transcript was stored; no booking    | The booking tool rejected `appliance repair` because the configured name is `Appliance repair` and matching was case-sensitive | Release 22 and a parametrized spoken-wording test |
| 2    | 06:31      | Agent could not follow the caller                         | Caller audio reached the microphone at about -30 dB                                                                            | Speaker and microphone levels fixed               |
| 3    | 06:43      | Requested time refused                                    | The caller gave no year, so the date fell outside the booking window                                                           | Caller script states the full date                |
| 4    | 06:45      | Availability failed with `oauth_revoked_or_scope_missing` | The Google refresh token had expired after 7 days because the OAuth app is in Testing                                          | Owner re-consent and release 23                   |
| 5    | 07:07      | Booked                                                    |                                                                                                                                |                                                   |

Call 5 in order: the opening-hours question abstained instead of guessing;
`check_availability` returned available; the caller confirmed; `create_booking`
stored booking `5f37df2c` for `Appliance repair` at 2026-10-27T14:00Z; the worker
completed the Google Calendar and CRM jobs and the event appeared in Google Calendar.
The follow-up email job ended as dead with `synthetic_recipient_required`. That is
intended: follow-ups go only to approved test recipients, and the synthetic caller's
example address is not one.

All five calls used the Retell free trial credit, at roughly USD 0.16 each. The
approved limit of five calls is used up; further calls need a new approval, billing
check and release.

## Verification

| Gate               | Result                                                                                          |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| Backend full suite | 258/258 passed on PostgreSQL with the release 22 change                                         |
| Static checks      | Mypy, Ruff and Bandit medium+ clean                                                             |
| Deployments        | Three guarded rollouts with backups, 16/16 files and 15/15 source modules each                  |
| Real flow          | Call 5 joined audio, ran two business tools and booked; Calendar and CRM jobs completed         |
| Review             | Fresh-context review approved release 22 and the release 23 token-rotation allowance with notes |

## Limits

- P09 in the [provider specification](../provider-interoperability-spec.md) is met for
  Retell only. The Vapi path has not been attempted, so P09 stays unchecked.
- The hours answer should have come from the business-hours document; retrieval needs work.
- The Google OAuth app is still in Testing, so refresh tokens expire after 7 days. No
  readiness check yet exercises the Google token before a call.
- One successful call is a functional result, not a reliability or capacity measurement.
  The original roadmap stays at 26/50 implementation and 0/30 readiness criteria.
- The synthetic test booking remains on the calendar.
