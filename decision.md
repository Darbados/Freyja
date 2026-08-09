# Decision: Centralize application email in a Mailer class

## Original idea

Application features should not call Django's email functions directly. Each
email subject or use case should have a named method on a `Mailer` class, and
callers should only instantiate that class and invoke the relevant method.

## Decision

Add `Freyja.mailer.Mailer` as the single boundary around Django's email API.
Provide named methods for leave requests, leave cancellations, and forgotten
password emails. Route Django's password-reset form hook through the Mailer as
well, so no feature code imports or calls the underlying mail API. Each method
owns a dedicated text or HTML template rather than constructing its email body
inline.
