# Public frontend redesign — acceptance criteria

Written before the redesign on 2026-10-07 after the user rejected the short
introduction. Preserve the approved operator dashboard design. Backend authentication, paid calls and real customer messaging are outside this
slice. Static publication was subsequently explicitly authorized after frontend
acceptance; its separate criteria are in frontend-deployment-spec.md.

1. W01: Home has a complete narrative: substantial hero, business-use strip,
   product showcase, scroll-driven workflow, capabilities, industry selector,
   integration section, FAQ, final action and full footer.
2. W02: Distinct complete Product, Solutions, Pricing, Company, Resources,
   Contact and Get Started destinations load by direct URL and browser history.
3. W03: Public navigation, footer and mobile navigation work with keyboard,
   Escape, visible focus and sensible focus return; every link has a destination.
4. W04: The hero has an animated 3D voice visual with a static fallback; motion
   can pause and respects reduced motion, document visibility and viewport.
   Changing the OS/browser motion preference updates a mounted page immediately.
5. W05: Scroll-linked progress/visual movement, section reveals, smooth section
   navigation and purposeful hover/page transitions run in actual Chrome.
6. W06: Pricing shows useful plan comparisons without invented prices, fake
   discounts, fabricated adoption figures, testimonials or compliance claims.
7. W07: Industry tabs, feature navigation, FAQ accordions and readable resource
   articles work; selected states are accessible and keyboard usable.
8. W08: Contact/get-started forms validate input and allow local review/editing;
   never claim an email was sent, an account created or payment taken.
9. W09: Public pages use business-oriented copy and make submission/call behavior clear at the relevant action.
10. W10: Existing twelve dashboard routes, design and linked-record interactions
    remain usable; permission and mutation validation remain enforced locally.
11. W11: All public pages and dashboard routes fit 375/768/1024/1440px; no clipped
    controls, missing assets or document overflow. Inspect full-page screenshots.
12. W12: No startup errors, CSP violations or unexpected external requests in browser replay.
    Presentation still embeds required assets and serves private paths as 404.
13. W13: New maintained copy/visual/motion configuration has one validated typed
    data/config owner. Registry/package integrity and advisories are checked.
14. W14: Tests, strict types, lint, formatting, security, build, real browser and
    fresh-context review results are reported. Actual Git/hook evidence and automatic-dispatch limits
    remain explicit; no production readiness, law/capacity/uptime claim.

Configuration inventory: public copy, navigation, plan descriptions, workflow,
industry/resource content, form labels and motion/3D visual parameters belong to
validated site data/settings. Protocol route identifiers belong to the protocol
module. Typography/colors/spacing stay in semantic CSS tokens; licensed fonts are
self-hosted. Renderer shaders and geometric invariants are protocol/math constants,
not product configuration. No credentials or external service execution required.

Research: current official Motion scroll, transform and accessibility guides;
Three.js installation/renderer documentation; installed UI UX Pro Max design-system
query. Preserve readable content and native scrolling under reduced motion.

Acceptance on 2026-10-07: W01–W14, 14/14 met for the frontend scope. Live Chrome
layout/motion/operator/CSP checks, full source gates and independent review pass.
See evidence/frontend-verification.md; no backend or production-service claim.
