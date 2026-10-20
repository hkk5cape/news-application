
The Dispatch - News Application

1. Clone the Project
Install Git first, then open PowerShell on Windows or a terminal on macOS/Linux:
```sh
git clone https://github.com/hkk5cape/news-application.git
cd news-application
```
Keep the terminal in this folder, beside `manage.py`. Choose either the virtual
environment route (sections 2-4) or Docker (section 5-10).

---
Option A – Manual Installation (Python + MariaDB)
2. Virtual Environment and Dependencies
This route needs Python 3.12 and a running MariaDB server.
Windows PowerShell
```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```
macOS/Linux
```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```
3. Create the Database and Private Configuration

Open the MariaDB client as a database administrator. Choose a local password and
replace `CHOOSE\\\_A\\\_LOCAL\\\_PASSWORD` below. These commands are SQL, not PowerShell:

```sql
CREATE DATABASE news\_app CHARACTER SET utf8mb4 COLLATE utf8mb4\_unicode\_ci;
CREATE USER 'news\_user'@'localhost' IDENTIFIED BY 'CHOOSE\_A\_LOCAL\_PASSWORD';
GRANT ALL PRIVILEGES ON news\_app.\* TO 'news\_user'@'localhost';
```
Run:
```sh
python scripts/configure.py
```
4. Start the Application
```sh
python manage.py migrate
python manage.py check
python manage.py runserver
```
Open http://127.0.0.1:8000/. Keep the terminal running; Ctrl+C stops the server.
Migrations initialise the role groups and permissions, not demonstration users.
With `DJANGO\\\_DEBUG=true`, Django serves CSS from `news/static/`. For a local style
problem, confirm `/static/news/style.css` loads and refresh the browser.

---
Option B – Docker Installation (Recommended)
1. Build and Run with Docker Compose

Docker Desktop must be running with Linux containers and Docker Compose v2.
No MariaDB installation on the host is needed for this route.
If Python is installed, create the container configuration:
```sh
python scripts/configure.py --docker
```
For Docker-only setup without host Python, use this instead in PowerShell:
```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/work" -w /work python:3.12-slim-bookworm python scripts/configure.py --docker
```
On macOS/Linux, the equivalent Docker-only command is:
```sh
docker run --rm --mount "type=bind,source=$(pwd),target=/work" -w /work python:3.12-slim-bookworm python scripts/configure.py --docker
```
The script generates three separate random secrets: the Django key, application
database password and MariaDB root password. It does not print them or create
users. If `.env` already exists, edit it rather than overwriting it; ensure it
contains `DB\\\_PASSWORD` and `MARIADB\\\_ROOT\\\_PASSWORD`.
Build and start:
```sh
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 240
docker compose ps
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
```
Both services should be healthy. Compose waits for MariaDB, runs migrations and
starts Django. Open http://127.0.0.1:8000/. If startup fails, inspect:
```sh
docker compose logs --tail 100 db web```

\---

## 2\. Write, Review, Subscribe and Send Newsletters

Journalists can create articles. Editors can approve articles and manage newsletters. Readers can subscribe to publishers and journalists.

\---

## 3\. Sphinx Documentation



Open **docs/\_build/html/index.html** directly in a browser. The generated HTML is
included in Git as specifically required by this assignment. Source guides and
Django-aware autodoc configuration are in `docs/`.

To rebuild from the project root in an activated environment:

```sh
python -m pip install -r requirements-docs.txt
python -m sphinx -W --keep-going -b html -d docs/.doctrees docs docs/\\\_build/html
```
Autodoc initialises `news\\\_project.settings` using SQLite for inspection. No
MariaDB connection or application accounts are needed to generate documentation.
---
4\. Run Tests
Windows PowerShell
```powershell
python -m pip install -r requirements-test.txt
$env:NEWS\_DB\_ENGINE = "sqlite"
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test news --verbosity 2
Remove-Item Env:NEWS\_DB\_ENGINE
```
macOS/Linux
```sh
python -m pip install -r requirements-test.txt
NEWS\_DB\_ENGINE=sqlite python manage.py check
NEWS\_DB\_ENGINE=sqlite python manage.py test news --verbosity 2
```
For tests against MariaDB, your database administrator must grant the application
user access to the separate `test\\\_news\\\_app` database before running the suite:
```sql
GRANT ALL PRIVILEGES ON test\\\_news\\\_app.\\\* TO 'news\\\_user'@'localhost';

\---

## 5\. API and Project Layout

``

POST `/api/token/` with a username and password to obtain a token. Use the private
header `Authorization: Token YOUR\\\_TOKEN` for API calls. The generated reference
lists article, approval, publisher, newsletter and profile endpoints.

```
Location                                         Purpose

news/`	                                         Models, forms, views, policies, services, API and tests
news/migrations/`	                               Database schema; keep these files in Git
templates/`, `news/templates/`	                 Application pages
news/static/`	                                   Application styling
news\\\_project/`	                               Django settings and project URLs								                 
Planning/`	                                     Existing design and Mermaid diagram sources
docs/`	                                         Sphinx sources, generated HTML and validation records
scripts/configure.py`	                           Private configuration generation
Dockerfile`, `                                   compose.yaml`	Container application and MariaDB service
SUBMISSION\\\_STEPS.md`, `capstone.txt`	         Publication and course submission


---
6\. Consolidated Git History
``
The original history is retained. The `docs` branch has separate documentation
commits for models, policies, forms, services and views plus the Sphinx build.
The `container` branch starts independently from `main`; both are merged into
`main` with merge commits. The README is committed after those merges.
```sh
git branch
git log --graph --oneline --all```
