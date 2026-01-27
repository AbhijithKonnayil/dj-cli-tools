from pathlib import Path
from typing import Optional

from django.core.management.base import CommandError


class FileHandlingMixin:
    """
    Mixin for Django management commands to handle file operations.
    Expected to be mixed in with BaseCommand.
    """

    def _get_file_path(self, app_config, filename: str) -> Path:
        return Path(app_config.path) / f"{filename}.py"

    def _read_file(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        try:
            return file_path.read_text(encoding="utf-8")
        except IOError as e:
            raise CommandError(f"Error reading file {file_path}: {e}")

    def _write_file(self, file_path: Path, content: str) -> None:
        try:
            file_path.write_text(content, encoding="utf-8")
        except IOError as e:
            raise CommandError(f"Error writing to file {file_path}: {e}")

    def _append_to_file(
        self,
        app_config,
        filename: str,
        template_code: str,
        success_message: str,
        import_statements: Optional[str] = None
    ) -> None:
        file_path = self._get_file_path(app_config, filename)
        
        if not file_path.exists():
            file_path.touch()

        current_content = self._read_file(file_path)
        
        new_content_parts = []
        
        # Prepend imports if they don't exist
        if import_statements and import_statements.strip() not in current_content:
            new_content_parts.append(import_statements)

        if current_content:
            new_content_parts.append(current_content)
            
        new_content_parts.append(template_code)
        
        # Join with double newlines for separation, ensure final newline
        final_content = "\n\n".join(part.strip() for part in new_content_parts if part.strip()) + "\n"
        
        self._write_file(file_path, final_content)

        if hasattr(self, 'stdout') and hasattr(self, 'style'):
            self.stdout.write(self.style.SUCCESS(success_message))
