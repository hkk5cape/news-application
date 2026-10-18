Installation
============

Download first
--------------

Install Git and Python 3.12, or Docker Desktop with Compose for the container
route. Open a terminal and run::

   git clone https://github.com/hkk5cape/news-application.git
   cd news-application

The README at the repository root contains the full copy-and-paste commands.

Virtual environment and MariaDB
-------------------------------

On Windows PowerShell::

   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt

On macOS/Linux::

   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt

The mysqlclient package needs MariaDB client development libraries when no wheel
is available. On Debian/Ubuntu, install build-essential, python3-dev,
default-libmysqlclient-dev and pkg-config before installing requirements.

In your MariaDB client, create a local database and user. Replace the sample
password with your own password; do not publish it::

   CREATE DATABASE news_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'CHOOSE_A_LOCAL_PASSWORD';
   GRANT ALL PRIVILEGES ON news_app.* TO 'news_user'@'localhost';

Return to the project terminal::

   python scripts/configure.py
   python manage.py migrate
   python manage.py runserver

The configuration script asks for that password and writes an ignored local
.env file. Migrations initialise role groups, not demonstration accounts.
Visit http://127.0.0.1:8000/ and register through the application.

Docker and MariaDB
------------------

In the cloned repository, generate local container configuration. Python 3.12
or the Docker-only command in the README can run this standard-library script::

   python scripts/configure.py --docker
   docker compose up --build -d
   docker compose logs -f web

The script generates separate random application, database and root secrets.
Compose starts MariaDB, waits for its health check, runs migrations and starts
the web application. Open http://127.0.0.1:8000/. Press Ctrl+C to leave logs;
containers continue running. Stop them with::

   docker compose down

The named database volume is retained. Do not remove that volume unless you
intend to delete the stored data. No users or passwords are included in Git.
This is a local course/demo server, not an Internet production deployment.

If configuration already exists
-------------------------------

The script refuses to overwrite .env. Edit it directly when switching from a
local database to Compose. Compose requires DB_PASSWORD and
MARIADB_ROOT_PASSWORD. Read .env.example for variable names and never commit
.env. Configure your email provider only if real inbox delivery is required;
the default backend prints email in the server logs.
