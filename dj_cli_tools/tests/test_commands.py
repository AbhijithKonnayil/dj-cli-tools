
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from dj_cli_tools.management.commands.create import Command as CreateModelCommand
from dj_cli_tools.management.commands.start_app import Command as StartAppCommand


class CreateModelCommandTests(TestCase):
    def setUp(self):
        self.app_name = "test_app"
        self.model_name = "TestModel"
        self.app_path = Path("/path/to/test_app")
        
        self.app_config_mock = MagicMock()
        self.app_config_mock.path = str(self.app_path)
        
    @patch("dj_cli_tools.management.commands.create_model.apps.get_app_config")
    @patch("dj_cli_tools.management.commands.create_model.Command._write_file")
    @patch("dj_cli_tools.management.commands.create_model.Command._read_file")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.touch")
    def test_create_model_success(self, mock_touch, mock_exists, mock_read_file, mock_write_file, mock_get_app_config):
        mock_get_app_config.return_value = self.app_config_mock
        mock_exists.return_value = True
        mock_read_file.return_value = ""
        
        call_command("create_model", self.app_name, self.model_name)
        
        # Verify models.py was written
        models_file = self.app_path / "models.py"
        self.assertTrue(any(call[0][0] == models_file for call in mock_write_file.call_args_list))
        
        # Verify serializers.py was written
        serializers_file = self.app_path / "serializers.py"
        self.assertTrue(any(call[0][0] == serializers_file for call in mock_write_file.call_args_list))

    @patch("dj_cli_tools.management.commands.create_model.apps.get_app_config")
    def test_create_model_app_not_found(self, mock_get_app_config):
        mock_get_app_config.side_effect = LookupError
        
        with self.assertRaises(CommandError):
            call_command("create_model", "non_existent_app", "Model")

class StartAppCommandTests(TestCase):
    @patch("dj_cli_tools.management.commands.start_app.StartAppCommand.handle")
    @patch("dj_cli_tools.management.commands.start_app.Command.find_directory")
    def test_start_app_with_template(self, mock_find_directory, mock_super_handle):
        mock_find_directory.return_value = "/path/to/template"
        mock_super_handle.return_value = None
        
        call_command("start_app", "my_app", dj_template="rest_version_app_template")
        
        mock_find_directory.assert_called_with("rest_version_app_template")
        # Check that template option was set
        call_args = mock_super_handle.call_args
        self.assertEqual(call_args[1]["template"], "/path/to/template")

    def test_start_app_conflict(self):
        with self.assertRaises(CommandError):
            call_command("start_app", "my_app", dj_template="t1", template="t2")

    @patch("dj_cli_tools.management.commands.start_app.settings")
    @patch("dj_cli_tools.management.commands.start_app.importlib.util.find_spec")
    @patch("dj_cli_tools.management.commands.start_app.os.environ.get")
    @patch("dj_cli_tools.management.commands.start_app.Command._get_app_config_name")
    def test_add_app_to_installed_apps(self, mock_get_config, mock_environ_get, mock_find_spec, mock_settings):
        mock_settings.configured = True
        mock_environ_get.return_value = "myproject.settings"
        mock_get_config.return_value = None # Fallback to simple name
        
        mock_spec = MagicMock()
        mock_spec.origin = "/path/to/settings.py"
        mock_find_spec.return_value = mock_spec
        
        with patch("dj_cli_tools.management.commands.start_app.Path") as MockPath:
            mock_path_instance = MagicMock()
            MockPath.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True
            
            # Case 1: Simple list
            mock_path_instance.read_text.return_value = "INSTALLED_APPS = [\n    'app1',\n]"
            
            cmd = StartAppCommand()
            cmd.stdout = MagicMock()
            cmd.style = MagicMock()
            
            cmd.add_app_to_installed_apps("new_app")
            
            mock_path_instance.write_text.assert_called()
            args = mock_path_instance.write_text.call_args[0][0]
            self.assertIn("'new_app',", args)
            self.assertIn("'app1',", args)

    @patch("dj_cli_tools.management.commands.start_app.settings")
    @patch("dj_cli_tools.management.commands.start_app.importlib.util.find_spec")
    @patch("dj_cli_tools.management.commands.start_app.os.environ.get")
    @patch("dj_cli_tools.management.commands.start_app.Path.cwd")
    def test_add_app_to_installed_apps_dotted(self, mock_cwd, mock_environ_get, mock_find_spec, mock_settings):
        mock_settings.configured = True
        mock_environ_get.return_value = "myproject.settings"
        
        mock_spec = MagicMock()
        mock_spec.origin = "/path/to/settings.py"
        mock_find_spec.return_value = mock_spec
        
        # Mock current working directory and apps.py
        mock_app_dir = MagicMock()
        mock_cwd.return_value = mock_app_dir
        mock_app_dir.__truediv__.return_value = mock_app_dir # Handle app_dir / app_name
        
        mock_apps_py = MagicMock()
        # We need to handle the chain: Path.cwd() / app_name / "apps.py"
        # The code does: app_dir = Path.cwd() / app_name; apps_py = app_dir / "apps.py"
        # So we need to mock the __truediv__ calls properly.
        
        mock_cwd.return_value = Path("/current/dir")
        
        with patch("dj_cli_tools.management.commands.start_app.Path") as MockPath:
            # We need to distinguish between settings path and apps.py path
            # This is tricky with a single MockPath. 
            # Let's rely on side_effect or return values based on input if possible, 
            # or just mock the specific instances if we can control them.
            
            # Easier approach: Mock the _get_app_config_name method? 
            # No, we want to test the whole flow if possible, but mocking Path is hard.
            # Let's mock _get_app_config_name for simplicity in this unit test, 
            # or be very careful with Path mocking.
            
            # Let's try mocking _get_app_config_name to isolate the settings update logic
            # and test _get_app_config_name separately? 
            # Or just mock Path carefully.
            
            mock_settings_path = MagicMock()
            mock_settings_path.exists.return_value = True
            mock_settings_path.read_text.return_value = "INSTALLED_APPS = []"
            
            # We need MockPath(spec.origin) to return mock_settings_path
            # And we need Path.cwd() to work.
            
            def path_side_effect(*args, **kwargs):
                if args and args[0] == "/path/to/settings.py":
                    return mock_settings_path
                return MagicMock() # For other paths
                
            MockPath.side_effect = path_side_effect
            
            # Now we need to mock the apps.py reading. 
            # Since we mocked Path, Path.cwd() is also affected if called as Path.cwd().
            # But we patched Path.cwd separately in the decorator? 
            # No, @patch("...Path.cwd") patches the cwd method on the Path class.
            # But we also patched the Path class itself with `with patch(...) as MockPath`.
            # This might conflict.
            
            # Let's avoid patching Path class entirely if we can, or use `new_callable`?
            # Actually, the code uses `Path(spec.origin)` and `Path.cwd()`.
            
            pass

    # Let's simplify. We can mock `_get_app_config_name` to return "MyAppConfig" 
    # to test the settings update part with dotted path.
    # And test `_get_app_config_name` separately.
    
    @patch("dj_cli_tools.management.commands.start_app.settings")
    @patch("dj_cli_tools.management.commands.start_app.importlib.util.find_spec")
    @patch("dj_cli_tools.management.commands.start_app.os.environ.get")
    @patch("dj_cli_tools.management.commands.start_app.Command._get_app_config_name")
    def test_add_app_to_installed_apps_dotted_integration(self, mock_get_config, mock_environ_get, mock_find_spec, mock_settings):
        mock_settings.configured = True
        mock_environ_get.return_value = "myproject.settings"
        mock_get_config.return_value = "MyAppConfig"
        
        mock_spec = MagicMock()
        mock_spec.origin = "/path/to/settings.py"
        mock_find_spec.return_value = mock_spec
        
        with patch("dj_cli_tools.management.commands.start_app.Path") as MockPath:
            mock_settings_path = MagicMock()
            MockPath.return_value = mock_settings_path
            mock_settings_path.exists.return_value = True
            mock_settings_path.read_text.return_value = "INSTALLED_APPS = []"
            
            cmd = StartAppCommand()
            cmd.stdout = MagicMock()
            cmd.style = MagicMock()
            
            cmd.add_app_to_installed_apps("new_app")
            
            mock_settings_path.write_text.assert_called()
            args = mock_settings_path.write_text.call_args[0][0]
            self.assertIn("'new_app.apps.MyAppConfig',", args)

    def test_get_app_config_name(self):
        cmd = StartAppCommand()
        with patch("dj_cli_tools.management.commands.start_app.Path.cwd") as mock_cwd:
            mock_app_dir = MagicMock()
            mock_cwd.return_value = mock_app_dir
            
            mock_apps_py = MagicMock()
            # app_dir / "new_app" / "apps.py"
            # The code is: app_dir = Path.cwd() / app_name; apps_py = app_dir / "apps.py"
            
            # Mocking the division operator behavior
            mock_app_path = MagicMock()
            mock_app_dir.__truediv__.return_value = mock_app_path
            mock_app_path.__truediv__.return_value = mock_apps_py
            
            mock_apps_py.exists.return_value = True
            mock_apps_py.read_text.return_value = "class MyAppConfig(AppConfig):"
            
            result = cmd._get_app_config_name("new_app")
            self.assertEqual(result, "MyAppConfig")
            
            # Test not found
            mock_apps_py.exists.return_value = False
            result = cmd._get_app_config_name("new_app")
            self.assertIsNone(result)
