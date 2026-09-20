# Observe leave requests in the backoffice

## Original idea and motivation

Administrators need `leaves_admin` to observe every leave request across Freyja. The
existing employee and manager views only expose requests within an individual or team
scope, leaving administrators without a reliable operational overview.

## Decision

Add a read-only, staff-protected, paginated endpoint under `/api/backoffice/leaves` and
place its serializer and view in the `backoffice.leaves_admin` package. Return employee,
approver, period, duration, type, status, comments, review and cancellation metadata,
and audit timestamps. Order requests by newest submission first and load related users
in the listing query.

Add a staff-only detail endpoint at `/api/backoffice/leaves/<id>` for direct links
to individual requests. The React backoffice provides separate list and detail
pages, including half-day portions and review/cancellation metadata.

Expose the data in the React backoffice as a dedicated Leave requests screen. Keep this
first slice observational: approval, rejection, cancellation, filtering, and export are
separate decisions rather than implicit administrative powers.
