# TOTP two-factor login

## Original idea and motivation

Add mandatory TOTP two-factor authentication to login in Freyja and Freyja-UI so a
stolen password is not sufficient to access an enrolled account.

## Decision

Keep TOTP enrollment and verification in Freyja. Every account must enroll during
its first successful password login or immediately after registration and confirm
ownership of an authenticator by entering a current six-digit code. Users cannot
disable the required factor themselves. Secrets are encrypted at rest with a key
derived from Django's secret key and are never returned after enrollment.
Enrollment returns a generated QR image rather than exposing the Base32 secret or
asking users to type it manually.

Password validation creates a five-minute, server-side session challenge rather than
an authenticated session. Only a valid TOTP code completes login. Existing accounts
must enroll before they can access the application.
Middleware also invalidates any authenticated session for an enrolled account that
lacks the verification marker, preventing legacy Django or admin login routes from
bypassing the second factor.
