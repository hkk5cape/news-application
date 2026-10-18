# The Dispatch - News Application

A Django publishing workspace for companies, editors and journalists. Editors
create a publisher, add employees and approve articles. Readers subscribe to
publishers and journalists. Normal application use does not require Django Admin.

## 1. Clone the project

Install Git first, then open PowerShell on Windows or a terminal on macOS/Linux:

```sh
git clone https://github.com/hkk5cape/news-application.git
cd news-application
```

Keep the terminal in this folder, beside `manage.py`. Choose either the virtual
environment route (sections 2-4) or Docker (section 5).

## 2. Virtual environment and dependencies

This route needs Python 3.12 and a running MariaDB server.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is blocked, use `.\.venv\Scripts\python.exe` instead of `python`
for each remaining Python command. No machine-wide policy change is needed.

macOS/Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If mysqlclient needs compiling, install your platform's compiler, Python headers,
MariaDB client development libraries and pkg-config. On Debian/Ubuntu:

```sh
sudo apt-get install build-essential python3-dev default-libmysqlclient-dev pkg-config
```

## 3. Create the database and private configuration

Open the MariaDB client as a database administrator. Choose a local password and
replace `CHOOSE_A_LOCAL_PASSWORD` below. These commands are SQL, not PowerShell:

```sql
CREATE DATABASE news_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'CHOOSE_A_LOCAL_PASSWORD';
GRANT ALL PRIVILEGES ON news_app.* TO 'news_user'@'localhost';
```

Exit the database client. In the project terminal run:

```sh
python scripts/configure.py
```

Enter the password you chose. This script creates `.env` with a random Django
secret key; it creates no mock accounts and refuses to overwrite existing
configuration. `.env.example` describes the variable names. Edit `.env` if your
database host or port differs. Never publish `.env`, passwords or API tokens.

## 4. Start the application with your virtual environment

```sh
python manage.py migrate
python manage.py check
python manage.py runserver
```

Open **http://127.0.0.1:8000/**. Keep the terminal running; Ctrl+C stops the server.
Migrations initialise the role groups and permissions, not demonstration users.
With `DJANGO_DEBUG=true`, Django serves CSS from `news/static/`. For a local style
problem, confirm `/static/news/style.css` loads and refresh the browser.

## 5. Build and run with Docker Compose

Docker Desktop must be running with Linux containers and Docker Compose v2.
No MariaDB installation on the host is needed for this route.

If Python is installed, create the container configuration:

```sh
python scripts/configure.py --docker
```

For Docker-only setup without host Python, use this instead in **PowerShell**:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/work" -w /work python:3.12-slim-bookworm python scripts/configure.py --docker
```

On **macOS/Linux**, the equivalent Docker-only command is:

```sh
docker run --rm --mount "type=bind,source=$(pwd),target=/work" -w /work python:3.12-slim-bookworm python scripts/configure.py --docker
```

The script generates three separate random secrets: the Django key, application
database password and MariaDB root password. It does not print them or create
users. If `.env` already exists, edit it rather than overwriting it; ensure it
contains `DB_PASSWORD` and `MARIADB_ROOT_PASSWORD`.

Build and start:

```sh
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 240
docker compose ps
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
```

Both services should be healthy. Compose waits for MariaDB, runs migrations and
starts Django. Open **http://127.0.0.1:8000/**. If startup fails, inspect:

```sh
docker compose logs --tail 100 db web
```

To observe console email, use `docker compose logs -f web`. Leave logs with Ctrl+C.
Stop the containers with `docker compose down`; the named database volume stays.
Changing `.env` later does not change passwords already stored in an existing
MariaDB volume. Use the existing credentials or deliberately create a separate
fresh installation. Do not delete a volume containing data you need.

The image runs as an unprivileged user and excludes local secrets, Git history
and virtual environments. This setup uses Django's development server for local
coursework; an Internet production deployment needs a production application
server, static-file serving, HTTPS and deployment-specific settings.

**Validation limit:** Docker and MariaDB runtime checks could not be executed in
the preparation environment. Run the commands above and the user walkthrough
before requesting review. SQLite tests do not substitute for that Docker check.

## 6. Create a publisher and its team

1. Click **Create an account** and register as **Editor** with your own password.
2. In **My publishers**, choose **Create publisher** and save the company profile.
   You automatically become its first editor.
3. Have colleagues register as **Journalist** or **Editor** with their own accounts.
4. Open your company and use **Add an employee** with a colleague's exact username.
5. Use **Edit publisher profile** and employee **Remove** actions as needed.
   The last active editor cannot be removed. Access is restricted to the company.

## 7. Write, review, subscribe and send newsletters

1. As a journalist, open **Newsroom -> Write article**, select your employer and
   save a draft. Leaving publisher blank creates independent reporting.
2. As an assigned editor, review it and choose **Approve / retry delivery**.
   Authors cannot approve their own articles. Drafts are hidden from readers.
3. The story appears in **Latest news**. Editing it returns it to draft status.
4. Readers register with the **Reader** role and use **Subscriptions** to follow
   publishers/journalists. **My subscriptions** filters their feed.
5. Editors and journalists can curate approved stories under **Newsletters** and
   use **Send / retry newsletter email**.
6. Approval emails subscribers and uses Requests to POST the approval event to
   `/api/approved/`. Retries skip deliveries already recorded as successful.
   Remote acceptance with a lost acknowledgement can still cause duplicates.

Use separate browser profiles or log out between roles. The default email backend
prints mail in the server terminal or container logs. Real inbox delivery requires
SMTP configuration in `.env`: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` and `DEFAULT_FROM_EMAIL`.
Never commit those credentials. No normal workflow requires a superuser;
`createsuperuser` and Django Admin are optional maintenance tools only.

## 8. Sphinx documentation

Open **docs/_build/html/index.html** directly in a browser. The generated HTML is
included in Git as specifically required by this assignment. Source guides and
Django-aware autodoc configuration are in `docs/`.

To rebuild from the project root in an activated environment:

```sh
python -m pip install -r requirements-docs.txt
python -m sphinx -W --keep-going -b html -d docs/.doctrees docs docs/_build/html
```

Autodoc initialises `news_project.settings` using SQLite for inspection. No
MariaDB connection or application accounts are needed to generate documentation.

## 9. Run tests

Portable verification without a MariaDB server, in PowerShell:

```powershell
python -m pip install -r requirements-test.txt
$env:NEWS_DB_ENGINE = "sqlite"
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test news --verbosity 2
Remove-Item Env:NEWS_DB_ENGINE
```

macOS/Linux:

```sh
python -m pip install -r requirements-test.txt
NEWS_DB_ENGINE=sqlite python manage.py check
NEWS_DB_ENGINE=sqlite python manage.py test news --verbosity 2
```

For tests against MariaDB, your database administrator must grant the application
user access to the separate `test_news_app` database before running the suite:

```sql
GRANT ALL PRIVILEGES ON test_news_app.* TO 'news_user'@'localhost';
```

Tests create temporary fixtures in their test database. No mock users are shipped.
See `docs/VALIDATION.md` for executed checks and `docs/MANUAL_TESTS.md` for the
complete acceptance walkthrough.

## 10. API and project layout

POST `/api/token/` with a username and password to obtain a token. Use the private
header `Authorization: Token YOUR_TOKEN` for API calls. The generated reference
lists article, approval, publisher, newsletter and profile endpoints.

| Location | Purpose |
| --- | --- |
| `news/` | Models, forms, views, policies, services, API and tests |
| `news/migrations/` | Database schema; keep these files in Git |
| `templates/`, `news/templates/` | Application pages |
| `news/static/` | Application styling |
| `news_project/` | Django settings and project URLs |
| `Planning/` | Existing design and Mermaid diagram sources |
| `docs/` | Sphinx sources, generated HTML and validation records |
| `scripts/configure.py` | Private configuration generation |
| `Dockerfile`, `compose.yaml` | Container application and MariaDB service |
| `SUBMISSION_STEPS.md`, `capstone.txt` | Publication and course submission |

## 11. Consolidation Git history

The original history is retained. The `docs` branch has separate documentation
commits for models, policies, forms, services and views plus the Sphinx build.
The `container` branch starts independently from `main`; both are merged into
`main` with merge commits. The README is committed after those merges.

```sh
git branch
git log --graph --oneline --all
```

The prepared archive includes `.git` so the branches and commits survive
extraction. Do not run `git init` again or upload individual files through the
GitHub web interface to replace this history. Follow **SUBMISSION_STEPS.md**.
