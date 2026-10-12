"""Create local configuration without demo accounts or hard-coded secrets."""

from getpass import getpass
from pathlib import Path
from secrets import token_urlsafe

root = Path(__file__).resolve().parent.parent
path = root / ".env"
if path.exists():
    raise SystemExit(".env already exists; edit it directly. Nothing was overwritten.")
password = getpass("Enter the MariaDB password you chose for news_user: ")
if not password or any(c in password for c in "\n\r"):
    raise SystemExit("A non-empty, single-line database password is required.")
# python-dotenv single-quoted values escape apostrophes and backslashes.
quoted = password.replace("\\", "\\\\").replace("'", "\\'")
path.write_text(
    f"DJANGO_SECRET_KEY={token_urlsafe(48)}\nDJANGO_DEBUG=true\n"
    "NEWS_DB_ENGINE=mariadb\nDB_NAME=news_app\nDB_USER=news_user\n"
    f"DB_PASSWORD='{quoted}'\nDB_HOST=127.0.0.1\nDB_PORT=3306\n"
    "API_BASE_URL=http://127.0.0.1:8000\nSITE_URL=http://127.0.0.1:8000\n"
    "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n",
    encoding="utf-8",
)
print("Created .env. Next: python manage.py migrate")
