"""Create private local configuration for a native or Docker installation."""

import argparse
import os
from getpass import getpass
from pathlib import Path
from secrets import token_urlsafe


def write_configuration(path, *, docker=False, password=None):
    """Create an exclusive .env file without overwriting existing credentials.

    Docker mode generates both database passwords. Native mode accepts the
    password already chosen by the user when creating their MariaDB account.
    The script depends only on Python's standard library.
    """
    if path.exists():
        raise FileExistsError(".env already exists; edit it directly.")
    if docker:
        password = token_urlsafe(32)
    if not password or any(character in password for character in "\n\r"):
        raise ValueError("A non-empty, single-line database password is required.")
    quoted = password.replace("\\", "\\\\").replace("'", "\\'")
    content = (
        f"DJANGO_SECRET_KEY={token_urlsafe(48)}\n"
        "DJANGO_DEBUG=true\nDJANGO_ALLOWED_HOSTS=localhost,127.0.0.1\n"
        "NEWS_DB_ENGINE=mariadb\nDB_NAME=news_app\nDB_USER=news_user\n"
        f"DB_PASSWORD='{quoted}'\nDB_HOST={'db' if docker else '127.0.0.1'}\n"
        "DB_PORT=3306\nAPI_BASE_URL=http://127.0.0.1:8000\n"
        "SITE_URL=http://127.0.0.1:8000\n"
        "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n"
    )
    if docker:
        content += f"MARIADB_ROOT_PASSWORD={token_urlsafe(32)}\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def main(argv=None):
    """Parse the install mode and create .env beside manage.py."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docker", action="store_true", help="Generate secrets for Docker Compose."
    )
    arguments = parser.parse_args(argv)
    path = Path(__file__).resolve().parent.parent / ".env"
    if path.exists():
        parser.exit(
            1, ".env already exists; edit it directly. Nothing was overwritten.\n"
        )
    password = None
    if not arguments.docker:
        password = getpass("Enter the MariaDB password you chose for news_user: ")
    try:
        write_configuration(path, docker=arguments.docker, password=password)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Configuration was not created: {error}\n")
    print("Created private .env; no application user accounts were created.")
    print(
        "Next: docker compose up --build -d"
        if arguments.docker
        else "Next: python manage.py migrate"
    )


if __name__ == "__main__":
    main()
