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
