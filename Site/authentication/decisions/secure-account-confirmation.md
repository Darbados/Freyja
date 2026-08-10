# Decision: Secure account-confirmation email links

## Original idea

Some account emails contain links that authorize sensitive actions. Account
confirmation and forgotten-password links must not trust editable identifiers
or unsigned URL parameters.

## Decision

Use Django timestamp signing for account-confirmation tokens with a dedicated
salt and a 24-hour maximum age. Bind the signed payload to both the user's ID and
current email address, making a later email change invalidate the link. Store the
confirmation timestamp on the user and make repeated confirmation idempotent.

Keep Django's existing password-reset token generator for forgotten-password
links. It is purpose-built to expire and become invalid after password or account
state changes, so replacing it with generic signing would weaken that flow.

Mailer receives only the completed confirmation URL and remains responsible for
templating and delivery, not token creation or verification.
