# Defect log

Record bugs discovered after an implementation was reported complete. Keep
existing rows and add the corrective gate and verification evidence.

| Date | What escaped | Which gate should have caught it | Gate added or improved? | Fix and verification |
| ---- | ------------ | -------------------------------- | ----------------------- | -------------------- |

| 2026-10-07 | Presentation URL delivered before real packaged bootstrap was exercised; global artwork substitution caused a startup ZodError and white screen | Packaged artifact integration and real-browser bootstrap | Added three artifact checks, artwork unit/component checks and full Chrome replay | Compiled data retained, separate PNG metadata; 47 application tests, 3 packaging checks, 52 layouts and 17 UI journeys pass |
| 2026-10-07 | Mobile document widened to 466px at a 375px viewport; banner action clipped | Responsive browser layout gate | Added document-width, image and banner-action checks across 52 route/viewport cases | Positioned table scroll container; mobile banner grows; Chrome layout checks pass |
| 2026-10-07 | Viewer native upload input remained enabled while its styled button was disabled | Browser permission and keyboard gate | Added native-input rendering regression and Viewer browser control checks | Native input disabled for Viewer/busy; independent review and browser replay pass |

| 2026-10-07 | Short introduction delivered as frontend left public pages and requested motion incomplete | Full page-map and client visual acceptance | Added W01–W14, eight public routes and complete-home/browser criteria | Public rebuild complete; latest live32 layouts/12 flows plus operator52/17 pass |
| 2026-10-07 | Mounted reduced-motion preference did not update animation behavior | Live preference-toggle browser gate | Added reactive preference regression and mounted browser toggle check | Reactive preference source and independent review pass; latest live mounted-toggle/pause/scroll journey passes |
| 2026-10-07 | Strict CSP initially blocked Zod code generation while UI still worked | Real deployed policy-event replay across every route | Added jitless facade, no-Function regression and per-route CSP accumulation | 70 source tests and live20-route replay pass with zero violations; release03 promoted with all6hashes matching |

| 2026-10-08 | Authenticated release used an unknown API environment variable and rendered blank | Exact packaged browser bootstrap before promotion | Artifact-bound passed status, login render, route/error/CSP checks required before promotion | Previous release restored; corrected packaged21routes pass and frontend05 live6fileparity/Googlelogin/native21routes pass |
| 2026-10-08 | Call could retire between tool authorization and booking reservation | Call authorization inside the tenant mutation lock | Added deterministic retirement-between-binding-and-booking regressions for both providers | Booking and read tools recheck retirement under the tenant lock;23focused checks/144backend tests andfreshintent review02pass; immutablebackend03publication inprogress |

| 2026-10-08 | Upgrade checker assumed raw Compose x-runtime mounts were resolved dictionaries and stopped before live mutation | Real resolved Compose-shape integration before publication | Added raw-extension readonly/writable/unrelated-mount regressions and strict known-preflight resume checks | Candidate upload/image retained; live02 unchanged;20upgrade/recovery regressions pass; freshresume reviewpending |
