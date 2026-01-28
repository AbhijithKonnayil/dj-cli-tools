from __future__ import annotations

import importlib.util
import os
import re
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
            
        directory = options.get("directory")
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        super().handle(*args, **options)
        
        if options.get("name"):
            self.add_app_to_installed_apps(options["name"], options.get("directory"))

    def _get_app_path(self, app_name, directory=None):
        if directory:
            return Path(directory)
        return Path.cwd() / app_name

    def _get_dotted_path(self, app_name, directory=None):
        if directory:
             # Calculate relative path from cwd to directory 
             # Assuming manage.py is in cwd or project root is cwd
             try:
                 rel = os.path.relpath(directory, os.getcwd())
                 if rel == '.':
                     return app_name
                 # If directory is inside cwd, convert path to module notation
                 # e.g. apps/my_app -> apps.my_app
                 base_module = rel.replace(os.path.sep, '.')
                 return base_module
             except ValueError:
                 # If directory is outside, default to app_name? 
                 # Or just assume app_name is what matters
                 return app_name
        return app_name

    def _get_app_config_name(self, app_path):
        # Try to find apps.py in the created app directory
        apps_py = app_path / "apps.py"
        
        if not apps_py.exists():
            return None
            
        content = apps_py.read_text()
        # Look for class MyAppConfig(AppConfig): or similar
        match = re.search(r"class\s+(\w+)\s*\([^)]*AppConfig[^)]*\):", content)
        if match:
            return match.group(1)
        return None

    def check_if_installed(self, app_name, app_config_path):
        if app_config_path in settings.INSTALLED_APPS:
             self.stdout.write(f"App '{app_config_path}' already in settings.")
             return True

        if app_config_path != app_name and app_name in settings.INSTALLED_APPS:
             self.stdout.write(f"App '{app_name}' already in settings (simple name).")
             return True
        return False

    def add_app_to_installed_apps(self, app_name, directory=None):
        if not settings.configured:
            return

        app_path = self._get_app_path(app_name, directory)
        dotted_base = self._get_dotted_path(app_name, directory)
        config_name = self._get_app_config_name(app_path)

        if config_name:
            # Update apps.py to include full dotted path in 'name'
            apps_py_path = app_path / "apps.py"
            if apps_py_path.exists():
                content = apps_py_path.read_text()
                # Check if name is just 'app_name' or something else
                # We want name = 'dotted_path'
                # Replace name = 'app_name' with name = 'dotted_base'
                # Usually template has name = '{{ app_name }}' which becomes name = 'app_name'
                new_name_line = f"    name = '{dotted_base}'"
                # Regex to replace indentation and name assignment
                content = re.sub(r"^\s*name\s*=\s*['\"][\w\.]+['\"]", new_name_line, content, flags=re.MULTILINE)
                apps_py_path.write_text(content)

            app_config_path = f"{dotted_base}.apps.{config_name}"
        else:
            app_config_path = dotted_base

        if self.check_if_installed(app_name, app_config_path):
             return

        settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
        if not settings_module:
            return
        try:
            spec = importlib.util.find_spec(settings_module)
            if spec is None or spec.origin is None:
                return
            settings_path = Path(spec.origin)
        except ImportError:
            return

        if not settings_path.exists():
            return
        content = settings_path.read_text()

        match = re.search(r"INSTALLED_APPS\s*(?:\+)?=\s*(\[|\()", content)
        if not match:
             # If INSTALLED_APPS is not defined in this file (e.g. imported from base),
             # append it to the end of the file.
             if isinstance(settings.INSTALLED_APPS, list):
                 append_str = f"\nINSTALLED_APPS += ['{app_config_path}']\n"
             else:
                 append_str = f"\nINSTALLED_APPS += ('{app_config_path}',)\n"
             
             settings_path.write_text(content + append_str)
             self.stdout.write(self.style.SUCCESS(f"Appended \'{app_config_path}\' to INSTALLED_APPS in settings.py"))
             return

        start_pos = match.end()
        open_bracket = match.group(1)
        close_bracket = ']' if open_bracket == '[' else ')'

        depth = 1
        end_pos = -1
        for i in range(start_pos, len(content)):
            if content[i] == open_bracket:
                depth += 1
            elif content[i] == close_bracket:
                depth -= 1
                if depth == 0:
                    end_pos = i
                    break

        if end_pos == -1:
            return

        last_line_start = content.rfind('\n', 0, end_pos) + 1
        last_line = content[last_line_start:end_pos]
        
        indent = "    "
        if last_line.strip() == "":
            indent = last_line + "    "
        
        pre_text = content[start_pos:end_pos].rstrip()
        needs_comma = False
        if pre_text and pre_text[-1] not in [',', open_bracket]:
            needs_comma = True

        insertion = ""
        if needs_comma:
            insertion += ","
        
        insertion += f"\n{indent}'{app_config_path}',"

        new_content = content[:end_pos] + insertion + content[end_pos:]
        settings_path.write_text(new_content)
        
        self.stdout.write(self.style.SUCCESS(f"Added \'{app_config_path}\' to INSTALLED_APPS in settings.py"))
