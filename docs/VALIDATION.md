# Consolidation verification record

Prepared: 18 October 2026. This record supersedes the earlier validation document
included in the input archive. It reports only checks executed for this revision.

Environment: Python 3.12.14, Django 5.2.18, Django REST Framework 3.16.1,
Sphinx 8.2.3. Tests used SQLite, not MariaDB.

## Passed here

| Check | Result | Evidence |
| --- | --- | --- |
| Django application tests | 57 passed, including 4 configuration tests | verification/django_tests.txt |
| Django system check | No issues | verification/django_check.txt |
| Migration drift check | No changes detected | verification/migration_drift.txt |
| Ruff configured code checks | Passed | verification/ruff.txt |
| Sphinx with warnings treated as errors | Passed | verification/sphinx.txt |
| Fresh SQLite migrations | All migrations applied | Executed against a disposable local database |
| Static-file collection | 164 files collected | Disposable generated files excluded from package |
| Generated HTML links/assets | All local targets exist | Static link validation |
| Compose YAML and service wiring | Parsed; database dependency and health checks present | Static inspection only |
| Application behaviour preservation | Five documented modules have identical ASTs after removing docstrings | Compared against baseline b1eaa8d |
| Git workflow | docs and container exist; five separate module commits; both branches merged | git log --graph --oneline --all |

The application tests cover publishing, role permissions, employee membership,
subscriptions, approvals, API access and delivery behaviour. Configuration tests
check password escaping, distinct generated secrets, refusal to overwrite an
existing .env and rejection of invalid passwords. No real credentials or accounts
are included in the deliverable.

## Required checks on the owner's machine

1. Build and run Docker Compose, including MariaDB migrations and web health.
2. Follow the application's manual user walkthrough in that installation.
3. Push main, docs and container to the existing public GitHub repository.
4. Verify the updated public repository through a fresh clone.
5. Upload the final project files and capstone.txt to the course dashboard.

Docker is not installed and no MariaDB server is available in this preparation
environment. Static Compose inspection does NOT establish that the image builds
or the services run. The README and SUBMISSION_STEPS.md provide exact runtime
commands. Public repository metadata was readable, but the connected GitHub
account did not have push permission; no publication is claimed.

Real SMTP inbox delivery depends on the owner's provider and was not tested.
The application's default email backend prints messages to the console. No new
browser screenshot or interactive user-journey check is claimed in this revision.
