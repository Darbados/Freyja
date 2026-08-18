# Organize tests by scope

## Original idea and motivation

The test suite used a single `tests.py` module in each app. As coverage grows,
mixing tests for unrelated application layers in one module makes tests harder
to locate, review, and extend.

## Decision

Use a `tests` package for each tested Django app and separate tests by the
application layer they exercise. View and API tests belong in `test_views.py`,
while model tests belong in `test_models.py`. Tests for another distinct scope
use an equally specific module, such as `test_mailer.py`. Each package includes
an `__init__.py` file so Django's test discovery treats it consistently as a
Python package. Create a scope module only when it contains tests; do not add
empty placeholder modules for scopes that are not covered yet.
