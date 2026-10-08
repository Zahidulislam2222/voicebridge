# Presentation bootstrap repair — 2026-10-07

Reproduction before implementation: Windows launcher starts, HTTP 200 serves the
generated artifact, but Chrome displays an empty body with ZodError at startup.
The packaging tool globally substitutes the artwork filename inside the compiled
product data, violating the deliberately strict relative-asset-path contract.

Acceptance criteria:

1. R01: Packaging retains the original compiled product data and embeds artwork
   separately; the strict asset-path contract is preserved.
2. R02: The packaged artifact loads the real React introduction in Chrome with
   no application startup error and displays a decoded artwork image.
3. R03: The original Windows launcher starts the preview; root HTTP returns 200,
   private file paths return 404, and rebuild/reload serves the corrected artifact.
4. R04: Automated packaging/asset regression checks, types, lint, build, security
   scans and fresh-context review are reported; the full browser journey resumes.
5. R05: Viewer-mode knowledge upload disables both the visible action and the
   native file input; browser and component checks reject a reachable upload
   control while keeping service-level authorization tests.

No new dependencies, provider calls, purchases or production deployment required.
