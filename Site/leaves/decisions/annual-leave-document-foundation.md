# Retain an unsigned PDF for every new annual-leave request

## Original idea and motivation

An employee's leave request should generate a document that they can later
sign electronically. The existing workflow only retained mutable request/profile
data and emailed an approver. We need a readable Bulgarian document whose exact
contents survive later profile changes, with a clear path to future signing.

## Decision

Implement the document-generation slice of the
[Bulgarian leave-document proposal](generate-signable-bulgarian-leave-documents.md).
New annual-leave requests create a frozen snapshot and a persistent render job in
one database transaction. The first rendering attempt runs after commit. Failure
keeps the request, snapshot and retryable job; it does not manufacture an empty or
signed document. Non-annual and historical requests have no generated document.
The existing pending/approval/cancellation workflow and Mailer notification remain.

Use a versioned Django text template and ReportLab layout with bundled, licensed
DejaVu fonts. This avoids introducing a native HTML-to-PDF service for one simple
A4 form. Fonts and templates are included in the Python package. Escape all
profile text before passing it to the PDF layout engine.

The document identifies the employer/EIK, addressee, employee's verified legal
name, personnel number and position, inclusive dates, working-day total, Article
155 basis, preparation date, document reference and template version. It reserves
space for a future employee signature. Comments and personal identifiers such as
EGN are excluded. The document contains no claim that leave has been approved.

Store PDF bytes privately in PostgreSQL with a SHA-256 digest and generated time.
For these small documents this gives atomic publication, existing backup coverage
and no public media URLs. List queries defer the PDF and snapshot columns.
The row is the durable job; `generate_leave_documents --limit 100` recovers pending
or failed work. Both the worker and retry endpoint lock the row, and a ready PDF
is never rendered again. Future object storage can preserve the same API.

Lock each employee during submission and accept a client UUID. Replays return the
same request; changed payloads with the same UUID return 409. Dates and identities
on documented requests cannot be changed through model/admin saves. Protected
relations prevent deleting the request, employment or employee with its retained
record. Cancellation changes workflow state while preserving the original PDF.
This is unsigned-document preservation; signed cancellation remains future work.

## Data and calendar prerequisites

Add an Employer entity and link it to Employment. HR must enter the employee's
legal name, personnel number and job title and explicitly confirm the supported
Bulgarian employment/weekday-calendar arrangement. Reject missing, ineligible or
ambiguous employment rather than guessing an employer or using an email as a name.
Existing records migrate with blank/unconfirmed data, so HR setup is a deployment
prerequisite for new annual requests.

Use the locked `holidays` Bulgarian calendar, including observed holidays, for
request duration, annual balance and the new authenticated estimate endpoint.
Store the actual working dates in the snapshot. API submissions are bounded to
367 calendar days. Annual leave takes whole days; half-days remain possible for
other existing categories, and historical half-day records remain readable and
cancelable. Calendar changes can correct the totals displayed for historical
requests; stored PDFs are never regenerated.

The foundation intentionally omits entitlement-year allocation from its wording:
there is no authoritative carryover/allocation ledger yet, and the year in which
leave is taken must not be presented as the year from which it is deducted.
The existing balance calculation is not an entitlement adjudication or an
allocation ledger. Add verified allocation before offering the full signing flow.

The original research supports a written employee request and separate employer
permission: [Labour Code Article 173](https://www.mlsp.government.bg/uploads/24/tpoout/kt.pdf)
and [ministry guidance on Article 22(2)](https://messages.mlsp.government.bg/messages/newm/index.php?ot=24&section=LIST&tid=1).
This PR implements the unsigned request only; employee signatures, employer QES,
consent, registered delivery, qualified timestamp evidence and legal retention
policy from the proposal remain subsequent work.

## API and access

- `POST /api/leaves/estimate`: same date/day-part validation and totals as creation.
- Existing create/list/cancel responses add nullable `document` metadata; creation
  accepts an optional `client_request_id` UUID (the companion UI always sends it).
- `GET /api/leaves/requests/<id>/document`: preparation status and metadata.
- `GET /api/leaves/requests/<id>/document/pdf`: retained PDF, or 409 before ready.
  `?download=1` requests attachment disposition. Responses are private/no-store.
- `POST /api/leaves/requests/<id>/document/retry`: idempotent rendering retry.

Document endpoints require a verified authenticated session and ownership,
assignment as leave approver, or `leaves.access_leave_documents`. General staff
status and department membership do not grant access. The backoffice exposes
metadata only to an authorized document reader. The UI displays pending/failed/
unsigned states, private preview/download and an explicit retry action. It does
not present a signing button or treat generated documents as signed.

## Deployment and validation

1. Install locked dependencies with `uv sync --extra dev` for testing, or `uv sync`
   for deployment, and apply the employment/leaves migrations.
2. In Django admin, create Employer entries, populate employee legal names,
   personnel numbers and positions, and assign employer/calendar settings on the
   single employment covering each employee's requested period.
3. Grant `access_leave_documents` only to the intended HR group. Employees and
   their assigned approvers do not need the global permission.
4. Deploy the companion UI after these backend APIs. Run
   `python Site/manage.py generate_leave_documents --limit 100` periodically in
   the deployment scheduler if automatic recovery after a process crash is needed;
   user retries work independently. Monitor job failures and database size.

Tests cover real Cyrillic PDF extraction, holiday/substitution/cross-year counts,
immutable bytes after profile changes, job recovery, idempotency and PostgreSQL
concurrency, object permissions, destructive edit/deletion protection, and
cancellation preservation. Validate standard and long-name layouts visually.
