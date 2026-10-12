# Validation — mentor feedback revision

Date: 11 October 2026. Python 3.12, Django 5.2.18, Django REST Framework 3.16.1.

## Executed checks

- 53 Django tests passed on SQLite, including 15 new publisher/onboarding tests.
  Full output: `test_results.txt`. Existing registration test now checks deliberate
  editor selection and rejects staff privilege escalation.
- Fresh SQLite migrations and static-file collection succeeded.
- `manage.py check` and `makemigrations --check --dry-run` passed; existing publisher
  membership tables support the new workflows without a schema change.
- Ruff code checks passed.
- Chromium browser automation against the running Django server passed registration
  for all three roles, company creation, automatic first-editor membership, adding
  a journalist, subscribing a reader, creating a company draft, denying draft access
  to the reader, approval and the real internal API POST, reading the published
  story, curating/sending a newsletter, employee removal and last-editor protection.
- Browser checks confirmed stylesheet HTTP 200, flex navigation, hidden skip link,
  keyboard activation focusing main content, and no horizontal overflow at 390px.
- Desktop (1440px), mobile (390px) and publisher-management screenshots were visually
  reviewed. Navigation is spaced, the publisher home introduction is readable, and
  the staff form is visible. Screenshots were internal inspection evidence, not
  additional submission files.

Browser-check accounts existed only in the disposable local database. No user
accounts, database files, passwords, virtual environment or collected static files
are included in the release archive. Unit tests create isolated test fixtures.

## Still to verify in the target environment

- MariaDB migrations and the suite against MariaDB (no server available here).
- The full manual acceptance checklist in `MANUAL_TESTS.md` on your own installation.
- Real SMTP delivery if you configure an external email provider. Console delivery
  was checked; inbox delivery is not claimed.
- Optional Docker Compose setup.
- Actual public GitHub publication and a fresh clone of that public repository.
- Removal of old snippets/archives from the course portal.

The README uses the intended public repository `Mickwen/news-application`. This
revision has not created or published that repository. Follow SUBMISSION_STEPS.md
before presenting the repository URL as a working link.
