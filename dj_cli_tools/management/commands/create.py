from pathlib import Path
from typing import Optional

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import models
import re

from dj_cli_tools.utils.case_utils import CaseUtils
from dj_cli_tools.utils.code_templates import CodeTemplates
from dj_cli_tools.utils.file_handling_mixin import FileHandlingMixin


class Command(FileHandlingMixin, BaseCommand):
    help = "Create a new model in the specified app"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "app_name", help="Name of the Django app to create the model in."
        )
        parser.add_argument(
            "model_name", help="Name of the model to create."
        )

    def handle(self, *args, **options):
        app_name = options["app_name"]
        model_name = options["model_name"]

        try:
            app_config = apps.get_app_config(app_name)
        except LookupError:
            raise CommandError(f"App '{app_name}' does not exist.")

        self._create_model(app_config, model_name)
        self._create_serializer(app_config, model_name)
        self._create_viewset(app_config, model_name)
        self._create_factory(app_config, model_name)
        self._register_admin(app_config, model_name)
        self._register_urls(app_config, model_name)

    def _create_model(self, app_config, model_name: str) -> None:
        model_name_pascal = CaseUtils.to_pascal_case(model_name)
        model_code = CodeTemplates.MODEL.format(model_name=model_name_pascal)
        success_message = f"Model '{model_name_pascal}' created in app '{app_config.name}'."
        self._append_to_file(
            app_config,
            'models', 
            model_code, 
            success_message=success_message
        )

    def _create_serializer(self, app_config, model_name: str) -> None:
        model_name_pascal = CaseUtils.to_pascal_case(model_name)
        serializer_name = f"{model_name_pascal}Serializer"
        
        serializer_code = CodeTemplates.SERIALIZER.format(
            serializer_name=serializer_name,
            model_name=model_name_pascal
        )
        imports = f"from rest_framework import serializers\nfrom .models import {model_name_pascal}"
        success_message = f"Serializer '{serializer_name}' created in app '{app_config.name}'."
        
        self._append_to_file(
            app_config,
            'serializers', 
            serializer_code, 
            success_message=success_message,
            import_statements=imports
        )

    def _create_viewset(self, app_config, model_name: str) -> None:
        model_name_pascal = CaseUtils.to_pascal_case(model_name)
        viewset_name = f"{model_name_pascal}ViewSet"
        serializer_name = f"{model_name_pascal}Serializer"

        viewset_code = CodeTemplates.VIEWSET.format(
            viewset_name=viewset_name,
            model_name=model_name_pascal,
            serializer_name=serializer_name
        )
        imports = (
            f"from rest_framework import viewsets\n"
            f"from .models import {model_name_pascal}\n"
            f"from .serializers import {serializer_name}"
        )
        success_message = f"ViewSet '{viewset_name}' created in app '{app_config.name}'."

        self._append_to_file(
            app_config,
            'views',
            viewset_code,
            success_message=success_message,
            import_statements=imports
        )

    def _create_factory(self, app_config, model_name: str) -> None:
        model_name_pascal = CaseUtils.to_pascal_case(model_name)
        factory_name = f"{model_name_pascal}Factory"

        factory_code = CodeTemplates.FACTORY.format(
            factory_name=factory_name,
            model_name=model_name_pascal
        )
        imports = (
            f"import factory\n"
            f"from .models import {model_name_pascal}"
        )
        success_message = f"Factory '{factory_name}' created in app '{app_config.name}'."

        self._append_to_file(
            app_config,
            'factories',
            factory_code,
            success_message=success_message,
            import_statements=imports
        )

    def _register_admin(self, app_config, model_name: str) -> None:
        model_name_pascal = CaseUtils.to_pascal_case(model_name)
        
        admin_code = CodeTemplates.ADMIN.format(model_name=model_name_pascal)
        imports = (
            f"from django.contrib import admin\n"
            f"from .models import {model_name_pascal}"
        )
        success_message = f"Registered '{model_name_pascal}' in admin for app '{app_config.name}'."

        self._append_to_file(
            app_config,
            'admin',
            admin_code,
            success_message=success_message,
            import_statements=imports
        )

    def _register_urls(self, app_config, model_name: str) -> None:
        model_name_pascal = CaseUtils.to_pascal_case(model_name)
        viewset_name = f"{model_name_pascal}ViewSet"
        # Convert PascalCase to snake_case for URL prefix
        url_prefix = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name_pascal).lower() + 's' 

        file_path = self._get_file_path(app_config, 'urls')
        if not file_path.exists():
            file_path.touch()
            # Initialize empty urls.py structure if strictly empty
            if file_path.stat().st_size == 0:
                 initial_content = CodeTemplates.URLS_INITIAL
                 file_path.write_text(initial_content, encoding="utf-8")

        content = self._read_file(file_path)
        
        # Check if router is defined
        if "router = DefaultRouter()" not in content and "router = SimpleRouter()" not in content:
            # Inject router definition
            imports_to_add = CodeTemplates.URLS_ROUTER_IMPORT
            if "import DefaultRouter" not in content:
                 content = imports_to_add + content
            
            router_def = CodeTemplates.URLS_ROUTER_DEF
            # Try to place it before urlpatterns
            if "urlpatterns =" in content:
                content = content.replace("urlpatterns =", router_def + "\nurlpatterns =")
            else:
                 content += router_def

        # Check for ViewSet import
        viewset_import = f"from .views import {viewset_name}"
        if viewset_name not in content:
            if "from .views import" in content:
                 # simplistic append to existing line could be tricky, 
                 # safest is to add new line for now or regex match key import block
                 # For robustness, we'll just prepend the specific import if missing
                 content = viewset_import + "\n" + content
            else:
                 content = viewset_import + "\n" + content

        # Register viewset
        register_line = f"router.register(r'{url_prefix}', {viewset_name})"
        if register_line not in content:
            # Find place to insert registration (after router definition)
            # We look for the router instantiation
            match = re.search(r"router\s*=\s*\w+Router\(\)", content)
            if match:
                 insertion_point = match.end()
                 content = content[:insertion_point] + f"\n{register_line}" + content[insertion_point:]
            else:
                 # Fallback if we can't find router instantiation easily but configured it separate
                 pass
        
        self._write_file(file_path, content)
        self.stdout.write(self.style.SUCCESS(f"Registered '{viewset_name}' in urls.py for app '{app_config.name}'."))
