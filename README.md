# The Dispatch — News Application

A publishing workspace for companies, editors and journalists. Editors create a
publisher profile, build their team, review articles and manage newsletters.
Readers can follow publishers and journalists and read approved reporting.
Normal use does not require Django Admin or a superuser.

## 1\. Download the project from GitHub

Prerequisites: Git, Python 3.12 and a running MariaDB server. Install these before
continuing. Open **PowerShell** on Windows or **Terminal** on macOS/Linux. Enter
one command at a time. Commands below assume this repository is published as
`Mickwen/news-application`; for a fork, use its HTTPS URL from GitHub's Code button.

```sh
git clone https://github.com/hkk5cape/news-application.git
cd news-application
```

You are now inside the project folder. It contains `manage.py`, `requirements.txt`
and this README. Keep this terminal in that folder for the remaining steps.
If Git reports “repository not found”, check the repository URL and that it is public.

## 2\. Create a virtual environment and install dependencies

A virtual environment keeps this project's Python packages separate.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell prevents activation, use `.\\.venv\\Scripts\\python.exe` instead of
`python` in subsequent commands. You do not need to change machine-wide policy.

macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If `mysqlclient` cannot build, install your operating system's compiler, Python
development headers, MariaDB client development libraries and pkg-config, then
retry installation. On Debian/Ubuntu these packages are `build-essential`,
`python3-dev`, `default-libmysqlclient-dev` and `pkg-config`.

## 3\. Create the MariaDB database

Open the MariaDB command-line client with your database administrator account.
This is database setup, not the application's Django Admin page. Run the following
SQL, replacing `CHOOSE\_A\_LOCAL\_PASSWORD` with a password you choose. Keep that
password for the next step; do not use the placeholder literally.

```sql
CREATE DATABASE news\_app CHARACTER SET utf8mb4 COLLATE utf8mb4\_unicode\_ci;
CREATE USER 'news\_user'@'localhost' IDENTIFIED BY 'CHOOSE\_A\_LOCAL\_PASSWORD';
GRANT ALL PRIVILEGES ON news\_app.\* TO 'news\_user'@'localhost';
```

Exit the database client and return to your project terminal. Run:

```sh
python scripts/configure.py
```

Enter the database password when prompted. It will not be displayed. The script
creates a local `.env` file and generates a random Django secret key. It does not
create users or overwrite existing configuration. For a remote database, edit
`DB\_HOST`, `DB\_PORT` and the other database values in `.env`.

## 4\. Initialise and start the application

```sh
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

Migrations create the database tables. A post-migration hook creates the Reader,
Editor and Journalist groups and assigns permissions automatically. **No mock
users are loaded.** Open **http://127.0.0.1:8000/** in your browser. Keep the terminal
open while using the application. Press Ctrl+C in it to stop the server.

The development server serves the application's CSS with `DJANGO\_DEBUG=true`.
If the page appears unstyled, check that `/static/news/style.css` loads, keep the
`news/static/` folder intact and refresh the browser. For production, a web server
must serve `STATIC\_ROOT` after `collectstatic`; this README describes local setup.

To start again later, enter the project folder, activate your virtual environment,
and run `python manage.py runserver`. A separate terminal is needed for other commands.

## 5\. Create your publishing company — no Admin panel

1. Click **Create an account**. Enter your username, email, a strong password and
select **Editor**. You will be taken to **My publishers**.
2. Click **Create publisher**. Enter your company name and description and save.
You are automatically added as its first editor.
3. Ask colleagues to register their own accounts as **Journalist** or **Editor**.
They choose their own passwords. You do not need to create accounts for them.
4. In **My publishers**, open your company. Under **Add an employee**, enter a
colleague's exact username and click **Add employee**. Repeat for your team.
Only registered, active editors and journalists can be added. Adding an editor
allows them to manage this company's profile, employees and editorial review.
5. Use **Edit publisher profile** to change the company description or name.
Use the employee's **Remove** button to remove their membership. Accounts and
stories are retained. The last active editor cannot be removed until another
active editor has been added. An editor cannot manage an unrelated company.

## 6\. Write, review and publish

1. A journalist logs in and opens **Newsroom → Write article**. Enter title and
content, select the publisher and save. Only their employers appear in the
publisher list. Leaving it blank creates independent reporting.
2. An editor for that company opens **Newsroom**, selects the draft, reviews it,
makes any needed edits, and clicks **Approve / retry delivery**. Editors can
also review independent articles. Drafts are hidden from readers.
3. The approved article appears under **Latest news**. Editing it returns it to
draft status until another approval. The normal pages provide edit and delete
actions with permission checks; deletion has a confirmation page.
4. Readers register with the **Reader** role, open **Subscriptions**, choose
publishers/journalists and save. They can select **My subscriptions** on home.
5. On approval, the service emails subscribers and uses Python Requests to POST
to this project's `/api/approved/` endpoint. This implements the brief's
**Option 2 (without approval signals)**. Role/group setup uses Django signals.
Delivery failures remain retryable without duplicate successful deliveries.
6. Editors and journalists open **Newsletters → Curate newsletter**, select
approved articles, save and use **Send / retry newsletter email**. Readers can view them.

The default email backend prints messages in the server terminal, so local setup
needs no email service. To deliver real mail, configure `EMAIL\_BACKEND` as
`django.core.mail.backends.smtp.EmailBackend` and set `EMAIL\_HOST`, `EMAIL\_PORT`,
`EMAIL\_HOST\_USER`, `EMAIL\_HOST\_PASSWORD`, `EMAIL\_USE\_TLS` and `DEFAULT\_FROM\_EMAIL`
in `.env`. Verify delivery with your provider. Keep credentials private.

Django Admin is optional maintenance only. A system maintainer may run
`python manage.py createsuperuser` for that purpose. None of steps 5–6 requires it.

## API reference

POST `/api/token/` with `username` and `password` obtains a token. Send the header
`Authorization: Token YOUR\_TOKEN` on API requests. Tokens are private credentials.

|Method and route|Purpose|
|-|-|
|GET `/api/articles/`|List approved articles|
|GET `/api/articles/subscribed/`|Reader's subscribed publishers/journalists|
|GET `/api/articles/<id>/`|Read an accessible article|
|POST `/api/articles/`|Journalist creates title, content, optional publisher ID|
|PUT/PATCH `/api/articles/<id>/`|Author or permitted editor updates article|
|DELETE `/api/articles/<id>/`|Author or permitted editor deletes article|
|POST `/api/articles/<id>/approve/`|Permitted editor approves article|
|POST `/api/approved/`|Record the approving editor's trusted event ID|
|GET `/api/publishers/`|List publishers|
|GET/POST `/api/newsletters/`|List/create newsletters according to role|
|GET/PUT/PATCH/DELETE `/api/newsletters/<id>/`|Newsletter operations by permission|
|GET `/api/me/`|Current user's role and applicable fields|

Publisher profile and employee management are provided through the web pages.
Tests in `news/tests.py` include API payload examples and access-control checks.

## Tests

In another activated project terminal:

```sh
python manage.py test news --verbosity 2
```

For MariaDB tests, your database administrator must grant the app user privileges
on the separate test database before running the command:

```sql
GRANT ALL PRIVILEGES ON test\_news\_app.\* TO 'news\_user'@'localhost';
```

For portable SQLite verification without a MariaDB server, install
`requirements-test.txt` and set `NEWS\_DB\_ENGINE=sqlite` only for that test run:

PowerShell:

```powershell
python -m pip install -r requirements-test.txt
$env:NEWS\_DB\_ENGINE="sqlite"
python manage.py test news --verbosity 2
Remove-Item Env:NEWS\_DB\_ENGINE
```

macOS/Linux:

```sh
python -m pip install -r requirements-test.txt
NEWS\_DB\_ENGINE=sqlite python manage.py test news --verbosity 2
```

See `docs/VALIDATION.md` for executed checks and remaining environment checks.
Follow `docs/MANUAL\_TESTS.md` to verify the complete user journey on your computer.

## Project files

* `news/`: models, forms, views, permissions, services, API, migrations and tests.
* `news/templates/` and `templates/`: application pages and shared layout.
* `news/static/news/style.css`: responsive styling and keyboard focus handling.
* `news\_project/`: settings and main URL configuration.
* `Planning/design.md`: requirements, database design and diagrams.
* `scripts/configure.py`: local configuration setup; creates no user accounts.
* `requirements\*.txt`, `.env.example`: dependencies and configuration reference.
* `Dockerfile`, `compose.yaml`: optional container setup. Copy `.env.example` to
`.env`, choose real local secrets/passwords, then run `docker compose up --build`.
This optional route has not been validated in the preparation environment.

Do not upload `.env`, databases, virtual environments or caches.

#   n e w s - a p p l i c a t i o n 
 
 
