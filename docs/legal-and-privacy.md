# Legal applicability, privacy and responsible voice use

This is an applicability and implementation register. Before each customer/region
release, assign an owner to verify entities, purposes, recipient locations,
provider contracts and legal decisions. Review date: 2026-10-08.

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
[EDPB guidance](https://www.edpb.europa.eu/sme_en). AI classification/transparency
review follows the [European Commission overview](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai).
Inbound service and outbound marketing need different applicability decisions;
the [FTC guide](https://www.ftc.gov/business-guidance/resources/complying-telemarketing-sales-rule)
identifies FCC/TCPA and state-law overlap. California assessment uses
[Attorney General guidance](https://oag.ca.gov/privacy/ccpa). Health deployments need
an independent [HIPAA applicability review](https://www.hhs.gov/hipaa/for-professionals/privacy/index.html).

## Data lifecycle

Inventory contacts, appointments, transcripts, recordings, knowledge, authentication
and operational events. Assign purpose, legal basis where required, roles, provider
destinations, retention and deletion owner. Avoid payment-card details, unnecessary
sensitive data and free-text secrets. Public evidence excludes client identities.

Before recordings, implement disclosure, consent/refusal, private retrieval and
enforced deletion of local/provider copies. Voice may be personal data; biometric
treatment depends on identification purpose and applicable law.

Provide access/correction/deletion/export/restriction/objection as applicable. Verify
requesters proportionately. Deletion covers replicas, indexes, queued work and
providers, with lawful holds and expiring backups documented. Do not promise immediate
erasure from immutable backups without the restore/deletion policy.

## Ownership and release gates

Customers approve business data, recipients, consent and communication purposes.
Maintainers own technical enforcement and gap records. Review provider terms,
subprocessors, locations, retention, incidents and voice-submission rights.
Emergency, diagnostic, credit, employment and other high-impact uses require their
own reviewed boundary. Booking automation does not authorize those decisions.

Publish customer-specific notices/agreements after confirming real data flows.
Include AI disclosure, human handoff, complaints, opt-out and incident procedures.
Track decisions in [the roadmap](roadmap.md); this register is not a blanket
certification for every jurisdiction or customer.
