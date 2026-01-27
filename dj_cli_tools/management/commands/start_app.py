from __future__ import annotations

from pathlib import Path
from typing import Optional

from django.conf import settings
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
                f"Could not locate dj_templates/{template_name} in repository parents")
        return str(template_dir)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--dj_template", help="Name of the application or project.")

    def handle(self, *args, **options):
        if options.get("dj_template") and options.get("template"):
            raise CommandError(
                "Cannot use --dj_template with --template option.")
        dj_template = options.pop("dj_template", None)
        if dj_template:
            dj_template_path = self.find_directory(dj_template)
            options["template"] = dj_template_path
            
        super().handle(*args, **options)
