# Bounded local capacity and reliability verification

The owner requested capacity/reliability testing alongside the core build on
7 October 2026, with no paid usage, damage or slowdown of other projects.

Acceptance: preserve other container identities/state; use a separate temporary
database and test-data recipients; perform no provider calls; cap concurrency,
request rate, duration, inserted rows and database connections; inspect host and
container resources before/after; stop at the configured CPU/memory/error/latency
threshold rather than escalating load automatically. Keep persisted evidence.

The initial admitted stage is deliberately small. Increase it only after the
previous stage passes and resource measurements support the next step. Testing
one million stored records is separate from one million dashboard sessions or
simultaneous paid calls. None can be inferred from a smaller run.

Uptime is a time-window observation, not a load-test score. Observe configured
health/booking indicators locally during a run, then report that run's duration,
successes/failures and restart recovery. Do not extrapolate to a 30-day 99.5% or
99.9% claim, or promise zero downtime. A single host remains a failure domain.

Profiles live in config/capacity-profiles.json. Retell/Vapi voice-call generation
is disabled for every local profile. Kubernetes is not required for the current
bounded checks and no cluster or server stress is authorized implicitly.
