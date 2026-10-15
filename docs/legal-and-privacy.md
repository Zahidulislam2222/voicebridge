# Legal applicability, privacy and responsible voice use

This is an applicability and implementation register. Before each customer/region
release, assign an owner to verify entities, purposes, recipient locations,
provider contracts and legal decisions. Review date: 2026-10-13. This register
identifies work for a specific release; it is not a jurisdiction-wide legal opinion.

| Area               | Applicability question                                          | Release evidence                                                                     |
| ------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| EU/EEA privacy     | Which controller/processor and people/purposes are in scope?    | Lawful basis, notice, minimization, rights, contracts, transfers and retention       |
| EU AI rules        | Intended use/risk class? Are people informed of AI interaction? | Classification, applicable transparency, prohibited-use screen and dated review      |
| US calls/marketing | Inbound service, outbound information or solicitation?          | Federal/state consent, suppression/opt-out, calling-time and identification review   |
| US recording       | Locations of participants and recorder?                         | Jurisdiction consent/disclosure decision and proof/withdrawal procedure              |
| California privacy | Business/statutory scope and covered processing?                | Rights/notice assessment, contracts and applicable sale/sharing controls             |
| Regulated sectors  | Covered health information or regulated advice?                 | Sector review, agreements and controls before accepting that data                    |
| Voice/media rights | Who owns/authorized voices, recordings and source material?     | Consent/licence scope, permitted use, duration, revocation and provider restrictions |

The EU register follows [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) and
[EDPB guidance](https://www.edpb.europa.eu/sme_en). Where the EU AI Act applies,
its Article 50 AI-interaction transparency requirements apply from 2 August 2026;
the [European Commission guidance](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act)
calls for a clear notice from the start of the first interaction. Review the
actual voice opening, accessibility and human-handoff path before enabling calls.
Inbound service and outbound marketing need different applicability decisions;
the [FTC guide](https://www.ftc.gov/business-guidance/resources/complying-telemarketing-sales-rule)
identifies FCC/TCPA and state-law overlap. California assessment uses
[Attorney General guidance](https://oag.ca.gov/privacy/ccpa). Health deployments need
an independent [HIPAA applicability review](https://www.hhs.gov/hipaa/for-professionals/privacy/index.html).

Recording and transcription need separate decisions. For example,
[Washington law](https://app.leg.wa.gov/RCW/default.aspx?cite=9.73.030)
generally requires consent of all participants to record private communications,
subject to its stated exceptions and announcement rules. Determine every
participant's location and the applicable rule before capture. Turning off stored
audio alone does not resolve transcription, vendor processing or notice duties.

## Data lifecycle

Inventory contacts, appointments, transcripts, recordings, knowledge, authentication
and operational events. Assign purpose, legal basis where required, roles, provider
destinations, retention and deletion owner. Avoid payment-card details, unnecessary
sensitive data and free-text secrets. Public evidence excludes client identities.

For each customer and provider, maintain a private processing map: controller and
processor roles; data category and purpose; lawful basis where required; collection,
storage and transfer locations; subprocessors and contracts; access roles; retention
period; and deletion evidence. GDPR processor arrangements and international
transfers require their own review under [Articles 28 and 44](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng).
Do not infer a suitable transfer mechanism from a provider's general marketing page.

Before recordings, implement disclosure, consent/refusal, private retrieval and
enforced deletion of local/provider copies. Voice may be personal data; biometric
treatment depends on identification purpose and applicable law.

Provide access/correction/deletion/export/restriction/objection as applicable. Verify
requesters proportionately. Deletion covers replicas, indexes, queued work and
providers, with lawful holds and expiring backups documented. Do not promise immediate
erasure from immutable backups without the restore/deletion policy.

The current owner-only local transcript redaction blocks late events from
restoring the local text. It does not establish deletion at Retell, Vapi, or in
historical backups. Verify provider deletion and replay safeguards before
claiming an end-to-end erasure workflow. Keep recordings, transcripts, provider
artifacts, contact records, knowledge, logs and backups on separately documented
retention schedules.

## Ownership and release gates

Customers approve business data, recipients, consent and communication purposes.
Maintainers own technical enforcement and gap records. Review provider terms,
subprocessors, locations, retention, incidents and voice-submission rights.
Emergency, diagnostic, credit, employment and other high-impact uses require their
own reviewed boundary. Booking automation does not authorize those decisions.

Publish customer-specific notices/agreements after confirming real data flows.
Include AI disclosure, human handoff, complaints, opt-out and incident procedures.
Assign an incident lead and processor contact. For a qualifying GDPR personal-data
breach, [Article 33](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) generally
requires controller notification to the competent authority without undue delay
and, where feasible, within 72 hours of awareness; assess the actual risk and any
other applicable deadlines rather than treating every event identically.
California rights and business applicability require a separate
[CCPA assessment](https://oag.ca.gov/privacy/ccpa). Outbound marketing and
informational calls require separate federal and state consent/opt-out reviews.
Track decisions in [the roadmap](roadmap.md); this register is not a blanket
certification for every jurisdiction or customer.

## AI output and communication review

Review both interaction notice and generated-output obligations. The European
Commission's [Article 50 guidance](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act)
distinguishes informing people of AI interaction from applicable machine-readable
marking/detectability duties for generated content. Establish the provider/deployer
role, exemptions, applicable dates and evidence with the selected voice provider;
an audible greeting alone is not the entire review.

For US communication, classify inbound assistance, informational outbound calls and
marketing separately. The [FCC AI-voice ruling](https://docs.fcc.gov/public/attachments/FCC-24-17A1.pdf)
addresses artificial/prerecorded voices under the TCPA. Review current consent,
identification, revocation, suppression, calling-time and federal/state overlap
before activation. Jurisdiction and participant location determine the recording
assessment; do not infer permission from a single state's rule.

## Download and rights-request handling

Local owner exports are authenticated, tenant scoped and bounded. The records
report excludes transcripts, credentials/private authorization records and raw job
payloads; a separate ended-call artifact handles local transcript access. Record
limits/counts/truncation are explicit. An owner download is an operational control,
not a complete jurisdiction-specific access-request response or a full backup.

Maintain a request process for identity verification, case ownership, response
scope/deadline, provider coordination, lawful exceptions and private receipts.
Downloaded copies require access/storage/retention handling by their recipient.
Redacting local text cannot recall already downloaded files, erase a provider's
recording or rewrite a historical backup. Verify deletion-after-restore behavior
and provider deletion separately. Keep only the necessary metadata in an audit.

## Decision record before customer activation

Record jurisdiction/customer purpose; controller/processor roles; AI and recording
notice; consent or other applicable legal basis; approved voice licence; provider
terms/subprocessors/transfers; retention/deletion schedule; rights/complaint route;
incident escalation and notification assessment. Revisit material changes in region,
provider, purpose or feature. Qualified legal review and signed customer decisions
remain release dependencies, not assertions created by publishing this register.
