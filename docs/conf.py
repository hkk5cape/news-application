"""Configure Sphinx and initialise Django without a database server."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["DJANGO_SETTINGS_MODULE"] = "news_project.settings"
# Autodoc inspects model definitions; it must not need MariaDB or real credentials.
os.environ["NEWS_DB_ENGINE"] = "sqlite"

import django  # noqa: E402

django.setup()

project = "The Dispatch - News Application"
author = "News Application Contributors"
copyright = "2026, News Application Contributors"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"]
exclude_patterns = ["_build", ".doctrees"]
html_theme = "alabaster"
html_title = project
html_theme_options = {"description": "Publishing, editorial review and subscriptions"}
autodoc_member_order = "bysource"
html_static_path = []
