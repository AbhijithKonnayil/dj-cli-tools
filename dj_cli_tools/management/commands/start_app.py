from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.startapp import Command as StartAppCommand


class Command(StartAppCommand):
    help = "Create a new Django app from the template"

    def find_directory(self, template_name):
        # Find the local `dj_templates/rest_version_app_template` by walking up the
        # parent directories from this file. This makes the command robust to
        # where the package is installed or executed from.
        current = Path(__file__).resolve()
        template_dir: Optional[Path] = None
        for p in current.parents:
            candidate = p / "dj_templates" / template_name
            if candidate.exists():
                template_dir = candidate
                break

        if template_dir is None:
            raise CommandError(
                "Could not locate templates/rest_version_app_template in repository parents")
        return str(template_dir)

    def handle(self, *args, **options):
        options["template"] = self.find_directory("rest_version_app_template")

        return super().handle(*args, **options)
