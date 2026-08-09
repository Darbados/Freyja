# Decision: Record the original idea behind every pull request

## Original idea

Every pull request should contain a `decision.md` file that captures why the
change was proposed. This gives future reviewers a durable way to recover the
original intent instead of inferring it only from the implementation.

## Decision

Add or update `decision.md` at the repository root in every pull request. Lead
with the original idea and motivation, then include only enough implementation
context to make the decision understandable later.
