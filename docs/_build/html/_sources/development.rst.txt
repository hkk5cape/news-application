Development and verification
============================

Build the documentation
-----------------------

From the project root, in an activated Python environment::

   python -m pip install -r requirements-docs.txt
   python -m sphinx -W --keep-going -b html -d docs/.doctrees docs docs/_build/html

Open docs/_build/html/index.html in a browser. The HTML is committed because this
assignment explicitly requires generated documentation. Only the intermediate
doctree cache is excluded. Configuration resolves the project root relative
to conf.py and initialises news_project.settings with SQLite for introspection;
it does not need MariaDB, user accounts or a database connection.

Run portable tests
------------------

Install requirements-test.txt, then on PowerShell::

   $env:NEWS_DB_ENGINE = "sqlite"
   python manage.py check
   python manage.py makemigrations --check --dry-run
   python manage.py test news --verbosity 2
   Remove-Item Env:NEWS_DB_ENGINE

On macOS/Linux::

   NEWS_DB_ENGINE=sqlite python manage.py check
   NEWS_DB_ENGINE=sqlite python manage.py test news --verbosity 2

For MariaDB tests, install requirements.txt and use a separate test database.
Your administrator must grant the user privileges on test_news_app; do not
change production permissions for a course test.

Git workflow
------------

The existing project history is preserved. The docs branch contains individual
commits for models, policies, forms, services and views before Sphinx generation.
The container branch starts from main and contains the runnable container setup.
Both branches are merged into main with merge commits. Review the record with::

   git log --graph --oneline --all
   git branch

The README and current validation record are committed after both merges.
See docs/VALIDATION.md for executed checks and remaining local checks. See
SUBMISSION_STEPS.md at the project root for publication and dashboard steps.
