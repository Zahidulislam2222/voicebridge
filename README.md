# VoiceBridge

AI voice receptionist and business automation: React/TypeScript frontend,
FastAPI/PostgreSQL core, durable workers and shared Retell/Vapi business tools.

**Website:** https://voicebridge.zahidul-islam.com/

**Author:** [Zahidul Islam](https://github.com/Zahidulislam2222)

## Capabilities

- Responsive public website with eight destinations and twelve operator destinations.
- Business console with Google OIDC, tenant/role checks, secure server sessions and CSRF protection.
- Availability, booking, rescheduling and cancellation with explicit confirmation,
  timezone validation, conflict prevention, idempotency and revision checks.
- Independent leased worker for calendar, CRM and follow-ups, with persisted retries,
  receipts, dead letters and explicit unknown-delivery states.
- Grounded knowledge with source revisions, bounded PDF parsing and abstention.
- Provider-authenticated Retell/Vapi tools, active-call scope and scoped MCP interfaces.
- Bounded owner records and local transcript downloads with tenant/role/CSRF checks and redaction protection.

## Implementation and roadmap

The single-business frontend and backend are deployed on the existing server.
The current guarded releases matched 16 backend and seven frontend files to
their live artifacts. The full 252-test backend suite exited successfully, and 108
frontend tests passed. One bounded owner-only booking previously received
direct Calendar and CRM readbacks and one authorized email confirmation.
Call creation is disabled; a separately gated owner recovery action verifies
the exact existing provider call before terminal retirement. The earlier
unjoined Retell call ended and its slot is clear; no conversation began.
Vapi creation and audio acceptance remain open. The twelve presentation/operator
destinations use controlled local state; `#/engine` is the persistent console.
The roadmap accepts 26/50 implementation and 0/30 readiness criteria. Unrestricted
external email remains disabled. See the [current release evidence](docs/evidence/tenant-export-release-20261015.md)
and [earlier release record](docs/evidence/pilot-verification.md).

The future architecture separately targets **1M+ registered accounts**, **1M+
active dashboard sessions** and **1M+ simultaneous voice calls**, plus a declared
mixed workload. None of these loads has been demonstrated. Reliability planning
sets a **99% baseline** and a **99.9% production objective** for defined service
indicators; neither is an achieved uptime figure or contractual SLA. The
[capacity roadmap](docs/capacity/scaling-roadmap.md) and
[reliability plan](docs/reliability.md) state the measurements required.

## Start developing

Prerequisites: Node 24.15+ within Node 24, Python 3.12–3.14 and PostgreSQL.
From the repository root:

```sh
npm ci
npm run dev
python -m venv .venv
# Activate the environment using your platform's standard command.
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
```

Populate an ignored `.env.local` from `.env.example`, configure a local PostgreSQL
instance and unique local credentials, then run:

```sh
python -m voicebridge.cli migrate --env-file .env.local
python -m voicebridge.cli seed --env-file .env.local
python -m voicebridge.cli api --env-file .env.local
```

Run `python -m voicebridge.cli worker --env-file .env.local` in a separate process.
Configure frontend API URL/origins from `.env.example` and open Business engine.
Keep real transports disabled in local development until their integration
acceptance. Backend tests have their own environment requirements described in
[testing](docs/testing.md).

## Guides

| Area                          | Documentation                                                                                                         |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Frontend/backend setup        | [Frontend](apps/web/README.md), [backend](apps/api/README.md)                                                         |
| Full documentation            | [Documentation index](docs/README.md)                                                                                 |
| Architecture and contracts    | [Architecture](docs/architecture.md), [API](docs/api/README.md)                                                       |
| Legal/privacy and security    | [Legal register](docs/legal-and-privacy.md), [security model](docs/security-model.md), [reporting](SECURITY.md)       |
| Future concurrency and uptime | [Scaling](docs/capacity/scaling-roadmap.md), [reliability](docs/reliability.md)                                       |
| Deployment and recovery       | [Deployment](deploy/README.md), [operations](docs/core-engine-operations.md), [runbooks](docs/operations-runbooks.md) |
| Delivery and contribution     | [Roadmap](docs/roadmap.md), [build plan](BUILD-PLAN.md), [contributing](CONTRIBUTING.md)                              |
| Rights and dependencies       | [LICENSE](LICENSE), [notices](THIRD-PARTY-NOTICES.md)                                                                 |

## Verification

```sh
npm test
npm run typecheck
npm run lint
npm run format:check
npm run presentation
npm run test:presentation
npm run test:release
npm run test:core-contracts
python -m pytest
python -m mypy
python -m ruff check apps/api tests
python -m bandit -q -ll -r apps/api
python -m build --no-isolation
```

CI uses standard public-repository runners; it does not invoke paid providers or
deploy services. Credentials, recovery records, browser captures and Google Doc/PDF
exports stay outside Git. Historical evidence remains dated to its actual scope.

## Public documentation program

[Documentation index](docs/README.md) covers architecture, HTTP/MCP contracts,
configuration, providers, legal/privacy applicability, security, monitoring,
runbooks and release evidence. [Future scaling](docs/capacity/scaling-roadmap.md)
separates stored accounts, active sessions, simultaneous calls and mixed workloads.
[Reliability](docs/reliability.md) defines99% and 99.9% objectives, indicators,
measurement and recovery acceptance. [Operations](docs/operations-runbooks.md)
and [publication criteria](docs/publication-20261015-spec.md) describe safe delivery.
