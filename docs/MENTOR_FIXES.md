# Mentor feedback mapping

| Feedback | Change |
| --- | --- |
| Loose duplicate snippets in portal | Clean project archive; obsolete BEFORE_SUBMITTING.txt removed. Actual portal cleanup remains an owner action in SUBMISSION_STEPS.md. |
| GitHub-first installation | README starts with clone and cd, then venv, dependencies, database, configuration and startup. Public repository publication still pending. |
| Admin-dependent functionality | Registration offers roles. Editors create/edit publishers and add/remove employees using normal application pages. |
| No mock account setup | Migration hook initialises role permissions; configure.py generates local configuration only. No seed users or databases shipped. |
| Focus on publishing companies | Publisher home introduction, My publishers navigation, newsroom onboarding and staff management. |
| Compressed header and skip link | Responsive navigation spacing, explicit static URL, focus-only skip link; browser and visual checks completed. |
| Publisher employees | Creator automatically joins as editor; existing editor/journalist accounts can be added by username; access scoped to company; last active editor protected. |

See docs/VALIDATION.md for executed tests and remaining environment checks.
