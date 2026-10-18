"""Exercise installation configuration without writing real project secrets."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from dotenv import dotenv_values

from scripts.configure import write_configuration


class ConfigurationTests(SimpleTestCase):
    def test_native_password_round_trips_special_characters(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            password = "an apostrophe ' and backslash \\ and # symbol"
            write_configuration(path, password=password)
            values = dotenv_values(path)
            self.assertEqual(values["DB_PASSWORD"], password)
            self.assertEqual(values["DB_HOST"], "127.0.0.1")
            self.assertNotIn("MARIADB_ROOT_PASSWORD", values)

    def test_docker_configuration_has_distinct_generated_secrets(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            write_configuration(path, docker=True)
            values = dotenv_values(path)
            self.assertEqual(values["DB_HOST"], "db")
            secrets = [
                values[key]
                for key in ("DJANGO_SECRET_KEY", "DB_PASSWORD", "MARIADB_ROOT_PASSWORD")
            ]
            self.assertTrue(all(len(secret) >= 32 for secret in secrets))
            self.assertEqual(len(set(secrets)), 3)

    def test_existing_configuration_is_never_overwritten(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("existing configuration", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_configuration(path, docker=True)
            self.assertEqual(path.read_text(), "existing configuration")

    def test_invalid_password_does_not_create_a_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            for password in (None, "", "two\nlines", "two\rlines"):
                with self.subTest(password=password):
                    with self.assertRaises(ValueError):
                        write_configuration(path, password=password)
                    self.assertFalse(path.exists())
