# Administrative user actions

## Original idea and motivation

Freyja administrators need to resend account-confirmation email and deactivate user
accounts from the backoffice without relying on Django's generic admin. These actions are
security-sensitive and will be initiated asynchronously by the React backoffice, so the
backend must remain authoritative and expose explicit commands with predictable results.

## Decision

Expose staff-only JSON endpoints under `/api/backoffice/users` for paginated user data,
details, confirmation-email delivery, and deactivation. Keep commands as POST endpoints
with no trailing slashes. Reuse the existing named `Mailer.send_account_confirmation`
email definition and signed confirmation-token implementation.

Centralize deactivation rules in a transactional service. Prevent self-deactivation,
protect superusers from ordinary administrators, and preserve the last active superuser.
Record confirmation requests and successful deactivations as immutable administrative
events containing the actor, target, target-email snapshot, action, and timestamp.
