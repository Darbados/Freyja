# Backoffice user details page

## Original idea and motivation

Backoffice operators need to move from the user list into an individual account and see
enough context to understand its identity, status, and recent activity. The page should
remain part of the extensible `users_admin` backoffice subapp and visually belong to the
existing Freyja backoffice.

## Decision

Add a staff-only detail view at `/backoffice/users/<id>` and link each email in the user
list to it. Present identity separately from account activity and access, including names,
email, username, join and confirmation dates, last sign-in, active state, and staff roles.
Do not expose password data or permission internals. Reuse the shared backoffice layout
and visual tokens so this page remains consistent with Freyja-UI and future detail pages.
