# Repository instructions

## Pull request decision record

- Every pull request must add or update `decision.md` at the repository root.
- Record the original idea and motivation for the pull request before describing
  the implementation.
- Keep the record focused on the decision being made so its intent remains clear
  when reviewing the pull request later.

## Python datetime imports

- Always import the `datetime` module with `import datetime`.
- Do not import individual members directly from `datetime`.
- Qualify all module members through `datetime`, for example:
  `datetime.date`, `datetime.datetime`, `datetime.time`, and
  `datetime.timedelta`.

## Email delivery

- Define every application email as a public method on `Freyja.mailer.Mailer`.
- Application code must call a named `Mailer` method and must not call Django's
  email functions or classes directly.
- Keep the direct Django email integration private to the `Mailer` class.
- Give every public mailing method its own dedicated `.txt` or `.html` message
  template; do not build email bodies inline in Python.
- Each public mailing method must fully construct its `EmailMessage` or
  `EmailMultiAlternatives` instance, including templates, subject, sender, and
  recipients. Pass the completed instance to `Mailer._send`, which should only
  call the message's `.send()` method.
- Define email subjects directly in their public mailing methods, optionally
  interpolating method parameters; do not render subjects from templates.
- Use a local variable named `msg` for the constructed `EmailMessage` or
  `EmailMultiAlternatives` instance.
- Keep message construction centralized so the transport can later migrate to
  `django-anymail` and `AnymailMessage` without changing feature code or public
  `Mailer` methods.
