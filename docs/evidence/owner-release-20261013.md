# Single-business release evidence — 2026-10-13

The current owner-scoped release is backend `20261013-native-owner-voice-14`
and frontend `20261013-native-frontend-08` on the existing shared server. The
guarded backend promotion verified 16/16 release-file hashes, 15/15 application
modules against its frozen image, ready health and preservation of 53 unrelated
containers. The frontend promotion verified seven/seven release files, the
owned gateway fragment and preservation of 13 unrelated gateway files. These
are point-in-time release checks, not sustained availability.

The frontend serves its committed artwork as a separate same-origin PNG. Local
and public HTTPS checks established gzip with `Vary: Accept-Encoding`, exact
decoded HTML and PNG bytes, and 21 packaged browser routes without application
or CSP errors. A fresh public load completed Google owner sign-in and showed
persisted bookings and the Calls panel with both male providers and the
60-second/one-call limits.

The backend keeps native account credentials and its recovery key in an
API-only runtime. The worker and observer receive voice-disabled settings.
Live provider-profile preflight compares the Retell agent and LLM and the Vapi
assistant with approved saved configurations; the two API model IDs now match
those configurations. A 15-minute free-credit receipt gates call creation.
Read-only account checks before the technical test showed Retell trial credits
of $10 with recharge off and Vapi credits of $5, no saved card, auto-reload off
and $0 monthly add-ons. These balances were checked at that time only.

One authenticated owner-only Retell web-call creation passed HTTP 200, returned
a browser grant and bound one call to the business record. No browser media was
joined and no conversation, audio quality, interruption, tool use or
voice-originated booking was verified. The provider still reported the call as
registered; its Stop Call API returned HTTP 400 in that state. The application
keeps the one-call slot occupied, so Vapi creation was not attempted. An
abandoned-before-join reconciliation path is an open defect. The owner deferred
personal listening. [Retell's web-call API](https://docs.retellai.com/api-references/create-web-call)
documents the expiring browser grant; its
[Stop Call API](https://docs.retellai.com/api-references/stop-call) applies to
ongoing calls. No second provider call was attempted.

Earlier bounded owner-only acceptance verified a Calendar event, Free CRM
contact and one Gmail confirmation for one booking, followed by Calendar
cancellation processed after worker restart. Current unrestricted external
follow-up delivery remains disabled. The dated details remain in
[pilot verification](pilot-verification.md).

The frontend package passed 97 tests, six release tests, four presentation
checks and 21 packaged Chromium routes. The full backend suite exited zero
after six deployment-inventory tests were added. Type, lint, build, scoped
Bandit, file-scoped Gitleaks and independent reviews passed in their recorded
scopes. The backend14 focused deployment-safety suite passed 53 checks. An
intermediate promotion reached ready health but rolled back when another
project changed ten containers on the shared server; canonical prior-release
parity was restored before backend14 passed a fresh baseline.

Future 1M+ account/session/call targets, 99% baseline, 99.9% production
service objective, regional legal applicability, off-device recovery and
commercial voice rights remain separate roadmap and verification work. The
[scaling roadmap](../capacity/scaling-roadmap.md),
[reliability plan](../reliability.md),
[legal register](../legal-and-privacy.md) and
[security model](../security-model.md) define their gates.
