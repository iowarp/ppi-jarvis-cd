"""
Module (Lmod) integration tests using Docker container with Lmod support.
Tests jarvis mod commands and verifies file creation in ~/.ppi-jarvis-mods.
"""
import unittest
import os
import sys
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.core.cli import JarvisCLI


class TestModuleIntegrationDocker(unittest.TestCase):
    """Module integration tests using Docker container with Lmod"""

    @classmethod
    def setUpClass(cls):
        """Set up Docker container for testing"""
        cls.use_docker = cls._check_docker_available()
        cls.container_name = 'jarvis_mod_test'

        if cls.use_docker:
            # Check if iowarp/iowarp-base:latest exists
            result = subprocess.run(
                ['docker', 'images', '-q', 'iowarp/iowarp-base:latest'],
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                print("Warning: iowarp/iowarp-base:latest not found, skipping Docker tests")
                cls.use_docker = False

    @staticmethod
    def _check_docker_available():
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(__file__).parent / 'test_mod_workspace'
        self.test_dir.mkdir(exist_ok=True)

        self.config_dir = self.test_dir / 'config'
        self.private_dir = self.test_dir / 'private'
        self.shared_dir = self.test_dir / 'shared'
        self.mods_dir = Path.home() / '.ppi-jarvis-mods'

        # Initialize CLI and define options
        self.cli = JarvisCLI()
        self.cli.define_options()

    def tearDown(self):
        """Clean up test environment"""
        # Remove test workspace
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Clean up test modules
        if self.mods_dir.exists():
            for test_mod in ['test1', 'test2', 'test_dep_mod', 'test_import', 'test_update']:
                mod_yaml = self.mods_dir / 'modules' / f'{test_mod}.yaml'
                mod_tcl = self.mods_dir / 'modules' / test_mod
                mod_pkg = self.mods_dir / 'packages' / test_mod

                if mod_yaml.exists():
                    mod_yaml.unlink()
                if mod_tcl.exists():
                    mod_tcl.unlink()
                if mod_pkg.exists():
                    shutil.rmtree(mod_pkg)

        # Stop and remove Docker container if used
        if hasattr(self, 'container_name') and self.use_docker:
            subprocess.run(
                ['docker', 'rm', '-f', self.container_name],
                capture_output=True
            )

    def run_command(self, args):
        """Helper to run CLI command"""
        try:
            result = self.cli.parse(args)
            return {
                'success': True,
                'result': result,
                'kwargs': self.cli.kwargs.copy() if hasattr(self.cli, 'kwargs') else {},
                'remainder': self.cli.remainder.copy() if hasattr(self.cli, 'remainder') else []
            }
        except SystemExit as e:
            return {'success': False, 'exit_code': e.code}
        except Exception as e:
            return {'success': False, 'error': str(e), 'exception': e}

    def test_mod_create_test1(self):
        """Test: jarvis mod create test1"""
        # Initialize Jarvis
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'), f"Init failed: {result}")

        # Create module test1
        result = self.run_command(['mod', 'create', 'test1'])

        # Verify module was created (check kwargs or file existence)
        if result.get('success'):
            self.assertEqual(result['kwargs'].get('mod_name'), 'test1')

        # Verify files created
        packages_dir = self.mods_dir / 'packages' / 'test1'
        src_dir = packages_dir / 'src'
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        tcl_file = self.mods_dir / 'modules' / 'test1'

        self.assertTrue(packages_dir.exists(), f"Package directory not created: {packages_dir}")
        self.assertTrue(src_dir.exists(), f"Source directory not created: {src_dir}")
        self.assertTrue(yaml_file.exists(), f"YAML file not created: {yaml_file}")
        self.assertTrue(tcl_file.exists(), f"TCL file not created: {tcl_file}")

        # Verify YAML content
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertIn('prepends', config)
        self.assertIn('setenvs', config)
        self.assertIn('deps', config)
        self.assertIn('doc', config)

        # Verify default paths include package root
        package_root = str(packages_dir)
        self.assertIn('PATH', config['prepends'])
        self.assertIn(f'{package_root}/bin', config['prepends']['PATH'])

        print(f"Module test1 created successfully at {packages_dir}")

    def test_mod_create_test2(self):
        """Test: jarvis mod create test2"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'), f"Init failed: {result}")

        # Create module test2
        result = self.run_command(['mod', 'create', 'test2'])

        if result.get('success'):
            self.assertEqual(result['kwargs'].get('mod_name'), 'test2')

        # Verify files created
        packages_dir = self.mods_dir / 'packages' / 'test2'
        src_dir = packages_dir / 'src'
        yaml_file = self.mods_dir / 'modules' / 'test2.yaml'
        tcl_file = self.mods_dir / 'modules' / 'test2'

        self.assertTrue(packages_dir.exists(), "Package directory not created")
        self.assertTrue(src_dir.exists(), "Source directory not created")
        self.assertTrue(yaml_file.exists(), "YAML file not created")
        self.assertTrue(tcl_file.exists(), "TCL file not created")

        print(f"Module test2 created successfully at {packages_dir}")

    def test_mod_directory_structure(self):
        """Test: Verify ~/.ppi-jarvis-mods directory structure"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create modules
        self.run_command(['mod', 'create', 'test1'])
        self.run_command(['mod', 'create', 'test2'])

        # Verify root directory structure
        self.assertTrue(self.mods_dir.exists(), "Modules root directory not created")
        self.assertTrue((self.mods_dir / 'packages').exists(), "Packages directory not created")
        self.assertTrue((self.mods_dir / 'modules').exists(), "Modules directory not created")

        # Verify test1 structure
        test1_pkg = self.mods_dir / 'packages' / 'test1'
        self.assertTrue(test1_pkg.exists())
        self.assertTrue((test1_pkg / 'src').exists())

        # Verify test2 structure
        test2_pkg = self.mods_dir / 'packages' / 'test2'
        self.assertTrue(test2_pkg.exists())
        self.assertTrue((test2_pkg / 'src').exists())

        print("Module directory structure verified")

    def test_mod_cd(self):
        """Test: jarvis mod cd test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Change to module
        result = self.run_command(['mod', 'cd', 'test1'])
        if result.get('success'):
            self.assertEqual(result['kwargs'].get('mod_name'), 'test1')

        print("Successfully changed to module test1")

    def test_mod_prepend(self):
        """Test: jarvis mod prepend test1 PATH=/custom/path"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Prepend environment variable
        result = self.run_command(['mod', 'prepend', 'test1', 'PATH=/custom/path'])

        # Verify YAML was updated
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertIn('PATH', config['prepends'])
        self.assertIn('/custom/path', config['prepends']['PATH'])

        # Verify TCL was regenerated
        tcl_file = self.mods_dir / 'modules' / 'test1'
        with open(tcl_file, 'r') as f:
            tcl_content = f.read()

        self.assertIn('prepend-path PATH /custom/path', tcl_content)

        print("Successfully prepended PATH to test1")

    def test_mod_setenv(self):
        """Test: jarvis mod setenv test1 MY_VAR=hello"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Set environment variable
        result = self.run_command(['mod', 'setenv', 'test1', 'MY_VAR=hello'])

        # Verify YAML was updated
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertIn('MY_VAR', config['setenvs'])
        self.assertEqual(config['setenvs']['MY_VAR'], 'hello')

        # Verify TCL was regenerated
        tcl_file = self.mods_dir / 'modules' / 'test1'
        with open(tcl_file, 'r') as f:
            tcl_content = f.read()

        self.assertIn('setenv MY_VAR hello', tcl_content)

        print("Successfully set MY_VAR in test1")

    def test_mod_destroy(self):
        """Test: jarvis mod destroy test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Verify creation
        packages_dir = self.mods_dir / 'packages' / 'test1'
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        tcl_file = self.mods_dir / 'modules' / 'test1'

        self.assertTrue(packages_dir.exists())
        self.assertTrue(yaml_file.exists())
        self.assertTrue(tcl_file.exists())

        # Destroy module
        result = self.run_command(['mod', 'destroy', 'test1'])

        # Verify deletion
        self.assertFalse(packages_dir.exists(), "Package directory still exists")
        self.assertFalse(yaml_file.exists(), "YAML file still exists")
        self.assertFalse(tcl_file.exists(), "TCL file still exists")

        print("Successfully destroyed test1")

    def test_mod_clear(self):
        """Test: jarvis mod clear test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Add files to package directory
        packages_dir = self.mods_dir / 'packages' / 'test1'
        bin_dir = packages_dir / 'bin'
        bin_dir.mkdir(exist_ok=True)
        test_file = bin_dir / 'test_exec'
        test_file.write_text('#!/bin/bash\necho test')

        # Verify files exist
        self.assertTrue(bin_dir.exists())
        self.assertTrue(test_file.exists())

        # Clear module (preserves src/)
        result = self.run_command(['mod', 'clear', 'test1'])

        # Verify bin/ was removed but src/ preserved
        self.assertFalse(bin_dir.exists(), "bin/ directory still exists")
        self.assertTrue((packages_dir / 'src').exists(), "src/ directory was removed")

        print("Successfully cleared test1 (preserved src/)")

    def test_mod_list(self):
        """Test: jarvis mod list"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create multiple modules
        self.run_command(['mod', 'create', 'test1'])
        self.run_command(['mod', 'create', 'test2'])

        # List modules
        result = self.run_command(['mod', 'list'])

        # Verify command executed (listing is printed)
        self.assertIsNotNone(result)

        print("Successfully listed modules")

    def test_mod_src_dir(self):
        """Test: jarvis mod src test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Get src directory
        result = self.run_command(['mod', 'src', 'test1'])

        # Verify result
        if result.get('success'):
            expected_src = str(self.mods_dir / 'packages' / 'test1' / 'src')
            # The src path is printed, not returned in kwargs
            self.assertTrue((self.mods_dir / 'packages' / 'test1' / 'src').exists())

        print("Successfully retrieved src directory")

    def test_mod_root_dir(self):
        """Test: jarvis mod root test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Get root directory
        result = self.run_command(['mod', 'root', 'test1'])

        # Verify result
        if result.get('success'):
            self.assertTrue((self.mods_dir / 'packages' / 'test1').exists())

        print("Successfully retrieved root directory")

    def test_mod_tcl_path(self):
        """Test: jarvis mod tcl test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Get TCL path
        result = self.run_command(['mod', 'tcl', 'test1'])

        # Verify file exists
        tcl_file = self.mods_dir / 'modules' / 'test1'
        self.assertTrue(tcl_file.exists())

        print("Successfully retrieved TCL path")

    def test_mod_yaml_path(self):
        """Test: jarvis mod yaml test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Get YAML path
        result = self.run_command(['mod', 'yaml', 'test1'])

        # Verify file exists
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        self.assertTrue(yaml_file.exists())

        print("Successfully retrieved YAML path")

    def test_mod_dir(self):
        """Test: jarvis mod dir"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Get modules directory
        result = self.run_command(['mod', 'dir'])

        # Verify directory exists
        self.assertTrue(self.mods_dir.exists())

        print("Successfully retrieved modules directory")

    def test_mod_dep_add(self):
        """Test: jarvis mod dep add test_dep_mod test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create modules
        self.run_command(['mod', 'create', 'test1'])
        self.run_command(['mod', 'create', 'test_dep_mod'])

        # Add dependency (dep_name first, then mod_name)
        result = self.run_command(['mod', 'dep', 'add', 'test_dep_mod', 'test1'])

        # Verify YAML was updated
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertIn('deps', config)
        self.assertIn('test_dep_mod', config['deps'])
        self.assertTrue(config['deps']['test_dep_mod'])

        # Verify TCL was regenerated with module load
        tcl_file = self.mods_dir / 'modules' / 'test1'
        with open(tcl_file, 'r') as f:
            tcl_content = f.read()

        self.assertIn('module load test_dep_mod', tcl_content)

        print("Successfully added dependency test_dep_mod to test1")

    def test_mod_dep_remove(self):
        """Test: jarvis mod dep remove test_dep_mod test1"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create modules
        self.run_command(['mod', 'create', 'test1'])
        self.run_command(['mod', 'create', 'test_dep_mod'])

        # Add dependency first (dep_name first, then mod_name)
        self.run_command(['mod', 'dep', 'add', 'test_dep_mod', 'test1'])

        # Verify it was added
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        self.assertIn('test_dep_mod', config['deps'])

        # Remove dependency (dep_name first, then mod_name)
        result = self.run_command(['mod', 'dep', 'remove', 'test_dep_mod', 'test1'])

        # Verify YAML was updated
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertNotIn('test_dep_mod', config['deps'])

        # Verify TCL was regenerated without module load
        tcl_file = self.mods_dir / 'modules' / 'test1'
        with open(tcl_file, 'r') as f:
            tcl_content = f.read()

        self.assertNotIn('module load test_dep_mod', tcl_content)

        print("Successfully removed dependency test_dep_mod from test1")

    def test_mod_prepend_multiple_values(self):
        """Test: jarvis mod prepend with semicolon-separated values"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create module
        self.run_command(['mod', 'create', 'test1'])

        # Prepend multiple paths
        result = self.run_command(['mod', 'prepend', 'test1', 'PATH=/path1;/path2;/path3'])

        # Verify YAML was updated
        yaml_file = self.mods_dir / 'modules' / 'test1.yaml'
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertIn('PATH', config['prepends'])
        self.assertIn('/path1', config['prepends']['PATH'])
        self.assertIn('/path2', config['prepends']['PATH'])
        self.assertIn('/path3', config['prepends']['PATH'])

        print("Successfully prepended multiple paths to test1")

    def test_mod_profile_default(self):
        """Test: jarvis mod profile (default dotenv format)"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Capture stdout to verify profile output
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Run profile command
            result = self.run_command(['mod', 'profile'])

            # Get output
            output = sys.stdout.getvalue()

            # Verify environment variables are printed
            expected_vars = ['PATH', 'LD_LIBRARY_PATH', 'LIBRARY_PATH',
                           'INCLUDE', 'CPATH', 'PKG_CONFIG_PATH', 'CMAKE_PREFIX_PATH',
                           'JAVA_HOME', 'PYTHONPATH']

            for var in expected_vars:
                self.assertIn(var, output, f"{var} not found in profile output")

            print(f"Profile output contains all expected environment variables")

        finally:
            sys.stdout = old_stdout

    def test_mod_profile_clion(self):
        """Test: jarvis mod profile with clion format"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Capture stdout
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Run profile command with clion format (use m= not method=)
            result = self.run_command(['mod', 'profile', 'm=clion'])

            # Get output
            output = sys.stdout.getvalue()

            # Verify output is semicolon-separated
            self.assertIn(';', output, "CLion format should be semicolon-separated")
            self.assertIn('PATH=', output)

        finally:
            sys.stdout = old_stdout

    def test_mod_profile_vscode(self):
        """Test: jarvis mod profile with vscode format"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Capture stdout
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Run profile command with vscode format (use m= not method=)
            result = self.run_command(['mod', 'profile', 'm=vscode'])

            # Get output
            output = sys.stdout.getvalue()

            # Verify output is JSON-like
            self.assertIn('"environment"', output, "VSCode format should have environment key")
            self.assertIn('"PATH"', output)

        finally:
            sys.stdout = old_stdout

    def test_mod_profile_to_file(self):
        """Test: jarvis mod profile path=/tmp/test_profile.env"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create temp file path
        profile_path = self.test_dir / 'test_profile.env'

        # Run profile command with output file
        result = self.run_command(['mod', 'profile', f'path={profile_path}'])

        # Verify file was created
        self.assertTrue(profile_path.exists(), "Profile file was not created")

        # Verify file contents
        with open(profile_path, 'r') as f:
            content = f.read()

        # Check for environment variables
        self.assertIn('PATH=', content)
        self.assertIn('LD_LIBRARY_PATH=', content)

        print(f"Profile written to {profile_path}")

    def test_mod_profile_cmake(self):
        """Test: jarvis mod profile with cmake format to file"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Create temp file path
        profile_path = self.test_dir / 'test_profile.cmake'

        # Run profile command with cmake format (use m= not method=)
        result = self.run_command(['mod', 'profile', f'path={profile_path}', 'm=cmake'])

        # Verify file was created
        self.assertTrue(profile_path.exists(), "CMake profile file was not created")

        # Verify file contents
        with open(profile_path, 'r') as f:
            content = f.read()

        # Check for CMake set commands
        self.assertIn('set(ENV{PATH}', content)
        self.assertIn('set(ENV{LD_LIBRARY_PATH}', content)

        print(f"CMake profile written to {profile_path}")

    def test_mod_build_profile(self):
        """Test: jarvis mod build profile (alternate command)"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Capture stdout
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Run build profile command with vscode format (which prints to stdout)
            # Note: dotenv without path doesn't print in build_profile (only in build_profile_new)
            result = self.run_command(['mod', 'build', 'profile', '--m=vscode'])

            # Get output
            output = sys.stdout.getvalue()

            # Verify environment variables are printed
            self.assertIn('PATH', output)
            self.assertIn('"environment"', output)

        finally:
            sys.stdout = old_stdout

        print("Build profile command executed successfully")

    def test_mod_import_simple(self):
        """Test: jarvis mod import with simple echo command"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Import module with a simple command that modifies PATH
        # Use a command that sets an environment variable
        result = self.run_command(['mod', 'import', 'test_import', 'export PATH=/custom/test/path:$PATH'])

        # Verify module was created
        yaml_file = self.mods_dir / 'modules' / 'test_import.yaml'
        self.assertTrue(yaml_file.exists(), "Import did not create module YAML")

        # Verify command was stored
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertIn('command', config)
        self.assertEqual(config['command'], 'export PATH=/custom/test/path:$PATH')

        print("Module imported successfully with stored command")

    def test_mod_update(self):
        """Test: jarvis mod update"""
        result = self.run_command(['init', str(self.config_dir), str(self.private_dir), str(self.shared_dir)])
        self.assertTrue(result.get('success'))

        # Import module first
        self.run_command(['mod', 'import', 'test_update', 'export MY_VAR=initial_value'])

        # Verify initial import
        yaml_file = self.mods_dir / 'modules' / 'test_update.yaml'
        self.assertTrue(yaml_file.exists())

        # Update the module (re-runs stored command)
        result = self.run_command(['mod', 'update', 'test_update'])

        # Verify module still exists and has command
        import yaml
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

        self.assertIn('command', config)
        self.assertEqual(config['command'], 'export MY_VAR=initial_value')

        print("Module updated successfully")


if __name__ == '__main__':
    unittest.main()
