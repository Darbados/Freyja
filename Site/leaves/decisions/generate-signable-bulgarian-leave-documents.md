# Generate signable Bulgarian leave documents

Status: broader design proposal. The unsigned generation slice is implemented by
[the foundation decision](annual-leave-document-foundation.md); signing and formal
submission/permission workflows remain proposed.
Research date: 11 October 2026. Jurisdiction: Bulgaria, confirmed by the user on
12 October 2026. This proposal covers employment relationships governed by the
Labour Code.

## Original idea and motivation

An employee's leave request should generate a document that the employee can later
electronically sign. Today Freyja saves the request and emails its approver, but
does not retain a document representing the employee's declaration. The proposed
design preserves the exact declaration, identifies the signer, and connects it to
the employer's subsequent permission without changing signed content.

## Recommended decision

Start with ordinary paid annual leave under Article 155. Generate a Bulgarian A4
PDF when a valid request is created, retain its immutable data snapshot, and show
it for review. Add electronic signing as a subsequent integration. The generated
PDF alone is not a signed request or permission to take leave.

Use two linked documents: the employee's request and the employer's permission.
This is a design choice, not a claim that the law requires two separate PDFs.
A combined, sequentially signed PDF is possible, but requires managing signature
permissions and later PDF revisions; separate documents are easier to preserve.

## Research and template references

| Reference | Useful elements | Treatment in Freyja |
| --- | --- | --- |
| [Sofia University leave form](https://www.uni-sofia.bg/index.php/bul/content/download/149450/1079842/version/1/file/zaiavlenie_za_otpusk_x2.pdf) | Addressee, employee, position, leave category, allocation year, dates, permission | Structural reference; omit university routing and duplicate paper copies |
| [ASO Trend annual-leave form](https://asotrend.bg/images/stories/docs/molba_platen_otpusk.pdf) | Compact employer/employee identification, requested days and dates, signature | Closest reference for a dedicated annual-leave request |

These are examples, not statutory certificates of compliance. Create our own
wording and layout. The provisions reviewed require written declarations and
permission, but do not prescribe the visual design used here. Employer-specific
rules and the final signing arrangement need Bulgarian employment-law review.

### Legal requirements that affect the design

- Annual leave needs written employer permission (Labour Code Article 173(1));
  Article 155 establishes annual leave in working days. Ordinary unpaid leave
  has a different basis (Article 160). Sick leave is authorized by health
  authorities (Article 162), so this application cannot replace a medical
  certificate. Interruption of leave also has specific rules (Article 175).
  [Labour Code, ministry publication](https://www.mlsp.government.bg/uploads/24/tpoout/kt.pdf).
- A written employee request is the basis for annual-leave permission under
  Article 22(2) of the working-time, rest and leave ordinance.
  [Ministry explanation](https://messages.mlsp.government.bg/messages/newm/index.php?ot=24&section=LIST&tid=1).
- Electronic personnel files require employee notification, documented consent
  to electronic statements and a withdrawal path; internal rules define document
  and signature types (Articles 3, 4, 6). Employee signatures follow law and
  agreement; employer documents require QES, and employer-required employee QES
  is employer-funded (Article 7). Record the employer signer's authority
  (Article 8). Register incoming documents and acknowledge number/date/time;
  distinguish acknowledgment email from electronic registered delivery of
  statements (Articles 4, 9). Support two-factor access, paper submissions,
  qualified timestamps for system actions, immutable receipt order, audit history,
  protected storage and free continuous employee access (Articles 10-14).
  [Electronic employment-file ordinance](https://www.mlsp.government.bg/uploads/37/politiki/trud/zakonodatelstvo/naredba-elektronno-dosie.pdf).
- A qualified electronic signature has the legal effect of a handwritten
  signature. This does not imply every employee signature must be qualified.
  [eIDAS, Article 25](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A02014R0910-20240520).
- Ministry guidance says annual leave is taken in whole working days, including
  for part-time employment. Disable half-day annual leave for this Bulgarian
  statutory template pending confirmation of any distinct applicable regime.
  [Ministry guidance, 14 January 2020](https://messages.mlsp.government.bg/arhiv/?page_no=3882).

The cited PDFs are the ministry's published references available during research;
the implementation review should verify amendments and employer-specific rules.

## Document design

The sample is `output/pdf/leave-document-design-bg.pdf`: two A4 pages showing two
separate proposed documents together for review. All names and identifiers are
illustrative. The production documents will be separate files.

### Employee request

Title: `ЗАЯВЛЕНИЕ за ползване на платен годишен отпуск`.

| Field | Purpose / source |
| --- | --- |
| Employer legal name and EIK, addressee | Identify the employing entity; new verified employer configuration |
| Employee full legal name | Add a verified legal-name field; do not use the current email-based display name |
| Employee number, position, department | Disambiguation and routing; snapshot existing profile plus new personnel number |
| Employment relationship | Persist selected employment internally; include contract reference if employer policy needs it |
| Legal basis and leave category | Versioned template mapping; Article 155 for this initial template |
| Inclusive start/end dates | Validated request dates |
| Working-day count | Authoritative Bulgarian calendar calculation, frozen with the document |
| Entitlement year allocation | Explicit year/day allocation; potentially several rows for carried-over leave |
| Request preparation date and document reference | Created locally in Europe/Sofia; signing/receipt times recorded separately |
| Employee signature area | Space for provider appearance; actual cryptographic signature is embedded by the signing integration |
| Template version | Trace which wording produced the artifact |

These are recommended identification and evidence fields, not a claim that each
is an individually mandated statutory field. Do not add EGN, home address, leave
reason, balance, or medical information by default. Free-text comments remain
internal unless explicitly selected for inclusion and previewed before signing.

Proposed core wording (our own draft):

> Моля да ми бъде разрешено ползването на платен годишен отпуск по чл. 155
> от Кодекса на труда за периода от [начална дата] до [крайна дата]
> включително, общо [брой] работни дни, от полагаемия ми се отпуск за
> [година / разпределение по години].

### Employer permission

Title: `РАЗРЕШЕНИЕ за ползване на платен годишен отпуск`.
Include its own reference/date, the received employee request reference and
version, employee, employer, identical period/day allocation, legal basis,
explicit permission, signer's full name/role and authority basis, and employer
QES. A requester's designated manager is not automatically a legally authorized
employer representative. A company seal is not a substitute for that signature.

Use restrained typography, a small employer header, a clear period/day summary,
and generous signature space. Embed Cyrillic fonts. Keep dynamic workflow badges
in the application; never stamp a new status onto an already signed PDF.

## Employee and approver experience

1. Employee enters dates and type, then selects **Create request**.
2. Request detail shows **Document being prepared**, followed by **Awaiting your
   signature**, a PDF preview, download, and the generation date/version.
3. When signing is available, **Review and sign** opens the exact stored PDF.
   A provider cancellation or failure leaves the document available for retry.
4. Successful validation and registered submission move the request into
   **Awaiting approval**. Send a receipt to the employee and notify the approver.
5. Employer reviews the signed request and signs the separate permission.
   Display **Approved - delivery pending** until delivery evidence is recorded,
   then **Approved - delivered**, with both original files downloadable.

Until signing is integrated, show **Unsigned document** with preview/download;
do not show a working signing button or infer signature from a normal submission.
Generation can initially accompany the existing workflow in a clearly marked
pilot. Enabling the formal workflow is a separate rollout and migration decision.

## Fit with the current code

- `Site/leaves/views.py`: creation saves `Leave` and schedules an approver email.
  Move orchestration into a service when implementation begins.
- `Site/leaves/models.py`: only pending/approved/rejected/canceled exist. Add
  explicit awaiting-signature and awaiting-employer-signature states for the
  formal workflow; never overload approved to mean employee-signed.
- `Site/leaves/models.py` and `balance.py`: weekdays are treated as eight hours,
  public holidays are not excluded, and half-days are accepted. Fix the common
  calculation service before it supplies legally used totals. Initially support
  standard Monday-Friday arrangements; route unsupported schedules for HR review.
- `Site/employment/models.py`: distinguish employment from civil contracts;
  `paid_leave_eligible` alone does not establish Labour Code coverage. Bind each
  request to the relevant employment and employer, including date eligibility.
- There is no verified employer identity, legal full-name field or leave-year
  allocation ledger in these models. Introduce those explicitly; do not infer
  allocation year from the date the leave is taken. Until a ledger is available,
  HR must verify allocation before the final document is offered for signing.
- `Site/authentication/middleware.py` already enforces verified TOTP sessions;
  reuse it for document access. Authentication itself does not sign a document.
- `Site/leaves/admin.py` currently exposes editable model administration. Prevent
  admin edits from bypassing signed-document/version and approval invariants.
- `Leave.employee` currently cascades deletion. Protect retained records and
  artifacts from accidental employee deletion, with explicit retention handling.
- The checked-out repository exposes backend APIs; coordinate UI changes with
  the separate frontend, rather than assuming its source is present here.

## Proposed backend design

Keep document ownership in `leaves`; extract shared infrastructure only when a
second application needs it.

| Component | Responsibility |
| --- | --- |
| `LeaveDocument` | Leave FK, UUID, kind, version, template version, language, frozen payload, creation actor/time, superseded-version link |
| `LeaveDocumentArtifact` | Original unsigned PDF, signed PDF or validation evidence; private storage key, SHA-256, size, creation time; append-only |
| `LeaveSignatureAttempt` | Signer identity/role, provider reference, expected document version/hash, attempt state, validation outcome and timestamps |
| `LeaveDocumentEvent` | Append-only generation, signing, submission, receipt, delivery and access evidence, with timestamp-service references |
| `Employer` / employment configuration | Legal identity, jurisdiction, authorized signers and effective authority, calendar policy |
| `ElectronicDocumentConsent` | Versioned scope, signature agreement, consent/withdrawal evidence; not a boolean inferred from using the app |
| Renderer | Produce PDF from the frozen payload and a versioned template |
| Signing/delivery adapters | Separate provider-specific calls from leave business rules |

Prefer a versioned Django HTML/CSS document template and a pinned PDF renderer
for production; assess the renderer in a small deployment spike. This visual
sample uses ReportLab only to make the proposal reviewable and adds no runtime
dependency. PDF/A and PAdES long-term-validation profiles are candidate archival
choices, not statutory format requirements asserted by this proposal.

Create request + snapshot + durable generation job in a database transaction.
An idempotent worker renders once and atomically publishes the stored artifact.
Use a durable outbox/worker with retries; `on_commit` alone is not a durable queue.
On failure retain the request and show a retryable preparation error. A repeated
client submission must not create duplicate requests or signing sessions.

Suggested additions to the existing API (names provisional):

- Request serializer: document status, current document ID/version and whether
  the authenticated actor may view, sign or regenerate.
- `GET /api/leaves/<id>/documents/` and protected artifact download endpoints.
- `POST /api/leaves/<id>/documents/<version>/signing-sessions/` in phase two.
- Authenticated, replay-protected provider callbacks; permission signing and
  registered-delivery endpoints are separate operations.

Freeze exactly the PDF offered for signature. Verify callback authenticity,
signer binding, signed byte ranges and unchanged content, document version,
certificate trust/status and timestamp evidence. The signed PDF necessarily has
different bytes from the unsigned one; compare the signed revision correctly,
not by requiring equality of whole-file hashes. Do not trust a browser redirect
as proof of signing. Reject stale callbacks after withdrawal or replacement.

Changing dates/type/identity/allocation produces a new version and requires a
new signature. Keep the old evidence and its supersession link. Never regenerate
historical downloads from current profile data. Allocate the official incoming
registration number on receipt, separately from the pre-signing document ID;
store the receipt without modifying the employee's signed PDF.

Use object-level authorization: employee, assigned authorized reviewer, and
explicit HR document roles. A department calendar or general staff listing must
not expose documents. Use private storage and access-controlled downloads, with
backup/restore and export of originals plus evidence. Determine retention with HR
and counsel; do not invent one universal period or auto-delete on account removal.

Signature, submission and delivery status remain distinct from the business
decision. Lock state transitions and entitlement reservations transactionally;
unsigned drafts do not permanently consume entitlement. Define expiry/recheck
rules for tentative reservations. Record timezone-aware UTC events and show
Bulgarian dates/times in Europe/Sofia, without backdating signatures.

All notifications remain named public `Mailer` methods with dedicated templates.
Methods construct `msg` and call `Mailer._send(msg)` under repository rules.
An ordinary email notification is not the registered-delivery adapter.

## Other leave types and later changes

Ordinary unpaid leave gets its own Article 160 template and validation. Sick leave
gets a medical-document receipt/notification workflow, not this permission
template. Replace generic Other with reviewed subtypes and their specific legal
bases and attachments. Civil contractors need contractual absence wording.

Withdrawal of an unsigned request can remain simple. Withdrawal of a signed
request preserves it and records a new declaration. Changes to approved leave
need a linked cancellation/amendment workflow; the existing immediate cancel
action must not silently invalidate a signed employer permission. Review the
rules for already-started leave before automating it.

## Delivery slices and acceptance checks

1. **Document foundation:** verified identities and employment binding, annual
   leave calendar/day policy and allocation, immutable snapshot/artifact, PDF
   generation, preview/download, retry handling. Output remains unsigned.
2. **Employee signing and submission:** provider adapter, consent, validated
   signatures, registration and receipt evidence, secure storage/access.
3. **Employer permission and delivery:** authority checks, QES, registered
   delivery, archival evidence and state transitions; enable formal workflow.
4. **Additional templates:** unpaid leave, supported special types and
   cancellation/amendment documents after their rules are specified.

Implementation checks should cover Bulgarian public holidays and substitution
days, whole-day validation, cross-year allocations, employment eligibility,
concurrent reservations, long Cyrillic names, unchanged historical documents,
cross-employee access, renderer retries, duplicate/out-of-order callbacks,
wrong signer/document, signature failure, withdrawal and supersession races,
delivery failure, and preservation through employee/account lifecycle changes.

Before production use, settle the employer identity and authority,
employee signature policy/provider, delivery/timestamp capabilities and retention.
The template can cover the declaration content; compliance also depends on the
operational signing, delivery and records process.
