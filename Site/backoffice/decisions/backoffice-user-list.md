# Backoffice user administration

## Original idea and motivation

Freyja needs a dedicated backoffice application that can grow a separate administrative
subapp for each product app. The first capability is a staff-only, paginated user list so
operators can review account email addresses, join dates, and email-confirmation status
without relying on Django's generic admin interface.

## Decision

Create `backoffice` as the top-level Django application and place user administration in
its `users_admin` Python package. Mount the application at `/backoffice`, with user
administration at `/backoffice/users`, and require Django staff access at the view
boundary.

Render the list as a server-side Django page with deterministic newest-first ordering and
50 users per page. Give the backoffice a shared base template and stylesheet based on the
Freyja-UI slate, cyan, translucent-panel, and rounded-control design language so future
backoffice subapps can reuse the same shell.
