# Testing and verification

Frontend gates: tests, TypeScript, ESLint, formatting, Vite build, exact browser
artifact and release/contract checks. Backend: pytest, strict Mypy, Ruff, Bandit,
Gitleaks, Semgrep and wheel/sdist. Advisory checks run before releases/lock changes.

## Install and verify commit hooks

Install pre-commit and provide `gitleaks`, `bandit` and Python on the commit process's
PATH. Semgrep must be installed on Linux; Windows commits use the installed WSL
Linux scanner through the public platform adapter. Windows also needs `wsl.exe`,
`wslpath` and a working Bash login environment that resolves Semgrep.
Use the versions exercised in publication evidence and verify their official
package/release sources when upgrading.

```sh
python -m pre_commit install
python -m pre_commit run --all-files
```

Verify that all three named scanner hooks actually run and pass. Do not bypass the
hook with disabled hooks or `--no-verify`. The public configuration uses system
tools, so installing pre-commit alone does not install each scanner. CI separately
installs pinned scanners; it is a backstop rather than a substitute for local hooks.

The backend suite loads `.local/core-engine/.env`. Configure an isolated loopback
PostgreSQL administrator allowed to create/drop generated `voicebridge_test_`
databases; never point it at production. Tests replace service credentials and
reject external sockets. CI creates its own PostgreSQL service and safe settings
from `.env.example`; real provider execution remains disabled.

Exercise actual HTTP/CLI/browser sign-in/CSRF/logout, booking retries/conflicts,
knowledge sources, worker lease/crash recovery, tenant/scope denial, provider
authentication and terminal retirement. Check the exact artifact and served CSP.
Restore separately and compare hashes/counts plus business behavior.

Native acceptance adds setup, intent/bind, audio, interruption, grounded answers,
tools, handoff, transcripts and end-call durability. Keep approved live samples
minimal; ordinary gates require no paid provider traffic.

Capacity uses guarded baseline/ramp/soak/failure scenarios within approved resource
limits. Publication checks worktree, staging, full history, private exclusions,
metadata and attribution; fresh-context review records scope and verdict.
Public CI uses standard Linux runners, minimal permissions and no production keys,
private uploads or automatic deployment. Counts remain dated to their evidence.
