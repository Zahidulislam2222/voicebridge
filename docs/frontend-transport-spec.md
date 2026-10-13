# Frontend transport acceptance

The authenticated frontend must load reliably through the existing public HTTPS
hostname. The current single-file HTML is approximately 5 MB because it embeds
an image already present as a committed asset. The next release extracts that
exact image, serves only its named URL, and compresses eligible HTML responses.

Acceptance criteria for the next frontend release:

1. A local request through the packaged Nginx configuration with a `Via`
   request header, `Accept-Encoding: gzip`, and the response's `no-store`
   policy returns `Content-Encoding: gzip` and `Vary: Accept-Encoding`.
2. The packaged HTML omits only the verified byte-identical embedded image tag.
   Its image request returns the committed PNG bytes at the single named route;
   unknown paths remain 404. Its CSP permits same-origin images, and the six
   legacy or seven artwork artifacts are the only accepted release inventories.
3. A client without gzip receives the exact packaged HTML bytes, and the
   compressed transfer decodes to that same hash. Inline script/style CSP hashes
   remain bound to the packaged bytes.
4. The new release passes existing frontend tests, type checking, lint,
   packaging checks, security scanning, and a fresh review.
5. Before publication, the current live files are snapshotted and compared to
   local. After publication, each release file matches local by SHA-256, the
   gateway and unrelated services remain unchanged, and the public HTTPS
   response proves gzip for an eligible GET.
6. A fresh browser load reaches the authenticated owner Calls view and renders
   the native-call panel without a page error. A provider call and human audio
   quality remain separate acceptance checks.

This transport change does not claim sustained uptime or future-scale capacity.
