"""
Comprehensive unit tests for jarvis_cd/core/pkg.py
Focuses on methods with low test coverage to improve overall coverage from 34% to 70%+
"""
import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.core.pkg import Pkg, Application, Service, Interceptor
from jarvis_cd.core.config import Jarvis


def initialize_jarvis_for_test(config_dir, private_dir, shared_dir):
    """Helper function to properly initialize Jarvis for testing"""
    # Get Jarvis singleton and initialize it
    jarvis = Jarvis.get_instance()
    jarvis.initialize(config_dir, private_dir, shared_dir, force=True)

    return jarvis


class TestPkgLoadStandalone(unittest.TestCase):
    """Test the load_standalone() class method"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_standalone_')
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        # Initialize Jarvis config
        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        # Reset Jarvis singleton
        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_load_standalone_with_full_spec(self):
        """Test load_standalone() with full package specification (repo.pkg)"""
        # Load example_app with full specification
        pkg = Pkg.load_standalone('builtin.example_app')

        self.assertIsNotNone(pkg)
        self.assertEqual(pkg.pkg_id, 'example_app')
        self.assertEqual(pkg.global_id, 'standalone.example_app')
        self.assertIsNotNone(pkg.pipeline)
        self.assertEqual(pkg.pipeline.name, 'standalone')
        self.assertIsNotNone(pkg.config_dir)
        self.assertIsNotNone(pkg.shared_dir)
        self.assertIsNotNone(pkg.private_dir)

    def test_load_standalone_with_package_name_only(self):
        """Test load_standalone() with just package name (searches repos)"""
        # This should find example_app in builtin repo
        pkg = Pkg.load_standalone('example_app')

        self.assertIsNotNone(pkg)
        self.assertEqual(pkg.pkg_id, 'example_app')
        self.assertEqual(pkg.global_id, 'standalone.example_app')

    def test_load_standalone_nonexistent_package(self):
        """Test load_standalone() with non-existent package"""
        with self.assertRaises(ValueError) as context:
            Pkg.load_standalone('nonexistent.package')

        self.assertIn('Repository not found', str(context.exception))

    def test_load_standalone_invalid_package_name(self):
        """Test load_standalone() with invalid package name"""
        with self.assertRaises(ValueError) as context:
            Pkg.load_standalone('completely_nonexistent_pkg')

        self.assertIn('Package not found', str(context.exception))

    def test_load_standalone_interceptor(self):
        """Test load_standalone() with interceptor package"""
        pkg = Pkg.load_standalone('builtin.example_interceptor')

        self.assertIsNotNone(pkg)
        self.assertIsInstance(pkg, Interceptor)
        self.assertEqual(pkg.pkg_id, 'example_interceptor')


class TestPkgEnvironmentMethods(unittest.TestCase):
    """Test environment manipulation methods"""

    def setUp(self):
        """Set up test environment with mock pipeline"""
        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_env_')
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_track_env_basic(self):
        """Test track_env() with basic environment variables"""
        pkg = Pkg(pipeline=self.mock_pipeline)

        env_dict = {
            'PATH': '/usr/bin:/bin',
            'MY_VAR': 'test_value',
            'ANOTHER_VAR': 'another_value'
        }

        pkg.track_env(env_dict)

        # Check that variables were added to env
        self.assertEqual(pkg.env['PATH'], '/usr/bin:/bin')
        self.assertEqual(pkg.env['MY_VAR'], 'test_value')
        self.assertEqual(pkg.env['ANOTHER_VAR'], 'another_value')

        # Check that mod_env is a copy of env
        self.assertEqual(pkg.mod_env['PATH'], '/usr/bin:/bin')
        self.assertEqual(pkg.mod_env['MY_VAR'], 'test_value')

    def test_track_env_with_ld_preload(self):
        """Test track_env() with LD_PRELOAD (should only go to mod_env)"""
        pkg = Pkg(pipeline=self.mock_pipeline)

        env_dict = {
            'PATH': '/usr/bin',
            'LD_PRELOAD': '/lib/interceptor.so'
        }

        pkg.track_env(env_dict)

        # LD_PRELOAD should NOT be in env
        self.assertNotIn('LD_PRELOAD', pkg.env)

        # But should be in mod_env
        self.assertEqual(pkg.mod_env['LD_PRELOAD'], '/lib/interceptor.so')

        # Other vars should be in both
        self.assertEqual(pkg.env['PATH'], '/usr/bin')
        self.assertEqual(pkg.mod_env['PATH'], '/usr/bin')

    def test_prepend_env_regular_variable(self):
        """Test prepend_env() with regular environment variable"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.env['PATH'] = '/usr/bin'
        pkg.mod_env['PATH'] = '/usr/bin'

        pkg.prepend_env('PATH', '/custom/bin')

        self.assertEqual(pkg.env['PATH'], '/custom/bin:/usr/bin')
        self.assertEqual(pkg.mod_env['PATH'], '/custom/bin:/usr/bin')

    def test_prepend_env_empty_variable(self):
        """Test prepend_env() when variable doesn't exist yet"""
        pkg = Pkg(pipeline=self.mock_pipeline)

        pkg.prepend_env('NEW_PATH', '/some/path')

        self.assertEqual(pkg.env['NEW_PATH'], '/some/path')
        self.assertEqual(pkg.mod_env['NEW_PATH'], '/some/path')

    def test_prepend_env_ld_preload(self):
        """Test prepend_env() with LD_PRELOAD (should only modify mod_env)"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.mod_env['LD_PRELOAD'] = '/lib/existing.so'

        pkg.prepend_env('LD_PRELOAD', '/lib/new.so')

        # LD_PRELOAD should NOT be in env
        self.assertNotIn('LD_PRELOAD', pkg.env)

        # Should be prepended in mod_env
        self.assertEqual(pkg.mod_env['LD_PRELOAD'], '/lib/new.so:/lib/existing.so')

    def test_setenv_regular_variable(self):
        """Test setenv() with regular environment variable"""
        pkg = Pkg(pipeline=self.mock_pipeline)

        pkg.setenv('MY_VAR', 'my_value')

        self.assertEqual(pkg.env['MY_VAR'], 'my_value')
        self.assertEqual(pkg.mod_env['MY_VAR'], 'my_value')

    def test_setenv_ld_preload(self):
        """Test setenv() with LD_PRELOAD (should only set mod_env)"""
        pkg = Pkg(pipeline=self.mock_pipeline)

        pkg.setenv('LD_PRELOAD', '/lib/interceptor.so')

        # LD_PRELOAD should NOT be in env
        self.assertNotIn('LD_PRELOAD', pkg.env)

        # Should be in mod_env
        self.assertEqual(pkg.mod_env['LD_PRELOAD'], '/lib/interceptor.so')

    def test_setenv_overwrites_existing(self):
        """Test setenv() overwrites existing values"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.env['VAR'] = 'old_value'
        pkg.mod_env['VAR'] = 'old_value'

        pkg.setenv('VAR', 'new_value')

        self.assertEqual(pkg.env['VAR'], 'new_value')
        self.assertEqual(pkg.mod_env['VAR'], 'new_value')


class TestPkgFindLibrary(unittest.TestCase):
    """Test find_library() method"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_lib_')
        self.lib_dir = os.path.join(self.test_dir, 'lib')
        os.makedirs(self.lib_dir, exist_ok=True)

        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_find_library_with_standard_name(self):
        """Test find_library() finds library with standard libXXX.so naming"""
        # Create a test library file
        lib_path = os.path.join(self.lib_dir, 'libtest.so')
        Path(lib_path).touch()

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.setenv('LD_LIBRARY_PATH', self.lib_dir)

        result = pkg.find_library('test')

        self.assertIsNotNone(result)
        self.assertEqual(result, lib_path)

    def test_find_library_with_so_extension(self):
        """Test find_library() finds library with .so extension"""
        lib_path = os.path.join(self.lib_dir, 'mylib.so')
        Path(lib_path).touch()

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.setenv('LD_LIBRARY_PATH', self.lib_dir)

        result = pkg.find_library('mylib')

        self.assertIsNotNone(result)
        self.assertEqual(result, lib_path)

    def test_find_library_static_library(self):
        """Test find_library() finds static library (.a)"""
        lib_path = os.path.join(self.lib_dir, 'libstatic.a')
        Path(lib_path).touch()

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.setenv('LD_LIBRARY_PATH', self.lib_dir)

        result = pkg.find_library('static')

        self.assertIsNotNone(result)
        self.assertEqual(result, lib_path)

    def test_find_library_not_found(self):
        """Test find_library() returns None when library not found"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.setenv('LD_LIBRARY_PATH', self.lib_dir)

        result = pkg.find_library('nonexistent')

        self.assertIsNone(result)

    def test_find_library_multiple_paths(self):
        """Test find_library() searches multiple paths in LD_LIBRARY_PATH"""
        lib_dir2 = os.path.join(self.test_dir, 'lib2')
        os.makedirs(lib_dir2, exist_ok=True)

        # Create library in second directory
        lib_path = os.path.join(lib_dir2, 'libfound.so')
        Path(lib_path).touch()

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.setenv('LD_LIBRARY_PATH', f'{self.lib_dir}:{lib_dir2}')

        result = pkg.find_library('found')

        self.assertIsNotNone(result)
        self.assertEqual(result, lib_path)

    def test_find_library_uses_mod_env(self):
        """Test find_library() checks mod_env for LD_LIBRARY_PATH"""
        lib_path = os.path.join(self.lib_dir, 'libmodenv.so')
        Path(lib_path).touch()

        pkg = Pkg(pipeline=self.mock_pipeline)
        # Set in mod_env directly (simulating LD_PRELOAD scenario)
        pkg.mod_env['LD_LIBRARY_PATH'] = self.lib_dir

        result = pkg.find_library('modenv')

        self.assertIsNotNone(result)


class TestPkgCopyTemplateFile(unittest.TestCase):
    """Test copy_template_file() method"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_template_')
        self.template_dir = os.path.join(self.test_dir, 'templates')
        os.makedirs(self.template_dir, exist_ok=True)

        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_copy_template_basic(self):
        """Test copy_template_file() with basic template"""
        # Create template file
        template_path = os.path.join(self.template_dir, 'test.txt')
        with open(template_path, 'w') as f:
            f.write('Hello World')

        dest_path = os.path.join(self.test_dir, 'output.txt')

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.copy_template_file(template_path, dest_path)

        # Verify file was copied
        self.assertTrue(os.path.exists(dest_path))
        with open(dest_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Hello World')

    def test_copy_template_with_replacements(self):
        """Test copy_template_file() with template replacements"""
        template_path = os.path.join(self.template_dir, 'config.xml')
        with open(template_path, 'w') as f:
            f.write('<config>\n  <host>##HOST##</host>\n  <port>##PORT##</port>\n</config>')

        dest_path = os.path.join(self.test_dir, 'config_output.xml')

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.copy_template_file(
            template_path,
            dest_path,
            replacements={'HOST': 'localhost', 'PORT': '8080'}
        )

        # Verify replacements were made
        with open(dest_path, 'r') as f:
            content = f.read()

        self.assertIn('<host>localhost</host>', content)
        self.assertIn('<port>8080</port>', content)
        self.assertNotIn('##HOST##', content)
        self.assertNotIn('##PORT##', content)

    def test_copy_template_creates_dest_directory(self):
        """Test copy_template_file() creates destination directory if needed"""
        template_path = os.path.join(self.template_dir, 'test.txt')
        with open(template_path, 'w') as f:
            f.write('Test content')

        # Destination in non-existent directory
        dest_path = os.path.join(self.test_dir, 'subdir', 'deep', 'output.txt')

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.copy_template_file(template_path, dest_path)

        # Verify file was created and directories were made
        self.assertTrue(os.path.exists(dest_path))

    def test_copy_template_with_numeric_replacements(self):
        """Test copy_template_file() with numeric replacement values"""
        template_path = os.path.join(self.template_dir, 'numeric.txt')
        with open(template_path, 'w') as f:
            f.write('Threads: ##THREADS##, Memory: ##MEMORY##MB')

        dest_path = os.path.join(self.test_dir, 'numeric_output.txt')

        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.copy_template_file(
            template_path,
            dest_path,
            replacements={'THREADS': 16, 'MEMORY': 4096}
        )

        with open(dest_path, 'r') as f:
            content = f.read()

        self.assertEqual(content, 'Threads: 16, Memory: 4096MB')

    def test_copy_template_file_not_found(self):
        """Test copy_template_file() raises error when template not found"""
        pkg = Pkg(pipeline=self.mock_pipeline)

        with self.assertRaises(FileNotFoundError):
            pkg.copy_template_file(
                '/nonexistent/template.txt',
                os.path.join(self.test_dir, 'output.txt')
            )


class TestPkgDisplayMethods(unittest.TestCase):
    """Test show_readme() and show_paths() methods"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_display_')
        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_show_readme_exists(self):
        """Test show_readme() when README.md exists"""
        # Use the actual example_app package which has pkg_dir set
        pkg = Pkg.load_standalone('builtin.example_app')

        # Create README in pkg_dir
        readme_path = os.path.join(pkg.pkg_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write('# Example App\n\nThis is a test README.')

        # Capture output
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            pkg.show_readme()

        output = f.getvalue()
        self.assertIn('Example App', output)
        self.assertIn('test README', output)

        # Clean up
        os.remove(readme_path)

    def test_show_readme_not_exists(self):
        """Test show_readme() when README.md doesn't exist"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.pkg_dir = self.test_dir

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            pkg.show_readme()

        output = f.getvalue()
        self.assertIn('No README found', output)

    def test_show_readme_no_pkg_dir(self):
        """Test show_readme() when pkg_dir is not set"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.pkg_dir = None

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            pkg.show_readme()

        output = f.getvalue()
        self.assertIn('Package directory not set', output)

    def test_show_paths_config(self):
        """Test show_paths() with conf flag"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.pkg_id = 'test_pkg'
        pkg._ensure_directories()

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            pkg.show_paths({'conf': True})

        output = f.getvalue()
        self.assertIn('config.yaml', output)

    def test_show_paths_multiple_flags(self):
        """Test show_paths() with multiple flags"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.pkg_id = 'test_pkg'
        pkg._ensure_directories()

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            pkg.show_paths({
                'conf_dir': True,
                'shared_dir': True,
                'priv_dir': True
            })

        output = f.getvalue()
        lines = output.strip().split('\n')

        # Should output 3 paths
        self.assertEqual(len(lines), 3)
        self.assertTrue(any('config' in line for line in lines))
        self.assertTrue(any('shared' in line for line in lines))
        self.assertTrue(any('private' in line for line in lines))

    def test_show_paths_pkg_dir(self):
        """Test show_paths() with pkg_dir flag"""
        pkg = Pkg.load_standalone('builtin.example_app')

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            pkg.show_paths({'pkg_dir': True})

        output = f.getvalue().strip()
        self.assertTrue(os.path.exists(output))
        self.assertIn('example_app', output)


class TestPkgConfigurationMethods(unittest.TestCase):
    """Test configuration-related methods"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_config_')
        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_apply_menu_defaults(self):
        """Test _apply_menu_defaults() applies default values from menu"""
        # Create a custom package class with menu
        class TestPkg(Pkg):
            def _configure_menu(self):
                return [
                    {'name': 'option1', 'default': 'default1'},
                    {'name': 'option2', 'default': 42},
                    {'name': 'option3', 'default': True}
                ]

        pkg = TestPkg(pipeline=self.mock_pipeline)
        pkg._apply_menu_defaults()

        self.assertEqual(pkg.config['option1'], 'default1')
        self.assertEqual(pkg.config['option2'], 42)
        self.assertEqual(pkg.config['option3'], True)

    def test_apply_menu_defaults_doesnt_overwrite(self):
        """Test _apply_menu_defaults() doesn't overwrite existing config"""
        class TestPkg(Pkg):
            def _configure_menu(self):
                return [
                    {'name': 'option1', 'default': 'default1'}
                ]

        pkg = TestPkg(pipeline=self.mock_pipeline)
        pkg.config['option1'] = 'existing_value'
        pkg._apply_menu_defaults()

        # Should not overwrite
        self.assertEqual(pkg.config['option1'], 'existing_value')

    def test_update_config(self):
        """Test update_config() method"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.config = {'existing': 'value'}

        pkg.update_config({'new_key': 'new_value', 'existing': 'updated'}, rebuild=False)

        self.assertEqual(pkg.config['new_key'], 'new_value')
        self.assertEqual(pkg.config['existing'], 'updated')

    def test_configure_menu_includes_common_params(self):
        """Test configure_menu() includes common parameters"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        menu = pkg.configure_menu()

        # Check for common parameters
        param_names = [item['name'] for item in menu]
        self.assertIn('interceptors', param_names)
        self.assertIn('sleep', param_names)
        self.assertIn('do_dbg', param_names)
        self.assertIn('timeout', param_names)

    def test_get_argparse(self):
        """Test get_argparse() returns PkgArgParse instance"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.pkg_id = 'test_pkg'

        argparse = pkg.get_argparse()

        self.assertIsNotNone(argparse)
        self.assertEqual(argparse.pkg_name, 'test_pkg')


class TestPkgUtilityMethods(unittest.TestCase):
    """Test utility methods like log(), sleep(), etc."""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_util_')
        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_sleep_with_config(self):
        """Test sleep() uses config value"""
        import time
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.config['sleep'] = 0.1

        start = time.time()
        pkg.sleep()
        elapsed = time.time() - start

        self.assertGreaterEqual(elapsed, 0.1)
        self.assertLess(elapsed, 0.2)  # Should not take much longer

    def test_sleep_with_parameter(self):
        """Test sleep() with explicit parameter overrides config"""
        import time
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.config['sleep'] = 10  # Would take too long

        start = time.time()
        pkg.sleep(time_sec=0.05)
        elapsed = time.time() - start

        self.assertGreaterEqual(elapsed, 0.05)
        self.assertLess(elapsed, 0.2)

    def test_sleep_zero(self):
        """Test sleep(0) completes immediately"""
        import time
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.config['sleep'] = 0

        start = time.time()
        pkg.sleep()
        elapsed = time.time() - start

        self.assertLess(elapsed, 0.01)

    def test_ensure_directories_creates_dirs(self):
        """Test _ensure_directories() creates all necessary directories"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.pkg_id = 'test_pkg'
        pkg._ensure_directories()

        self.assertTrue(os.path.exists(pkg.config_dir))
        self.assertTrue(os.path.exists(pkg.shared_dir))
        self.assertTrue(os.path.exists(pkg.private_dir))

    def test_ensure_directories_idempotent(self):
        """Test _ensure_directories() can be called multiple times safely"""
        pkg = Pkg(pipeline=self.mock_pipeline)
        pkg.pkg_id = 'test_pkg'

        pkg._ensure_directories()
        dir1 = pkg.config_dir

        pkg._ensure_directories()
        dir2 = pkg.config_dir

        self.assertEqual(dir1, dir2)


class TestPkgSubclasses(unittest.TestCase):
    """Test Service, Application, and Interceptor subclasses"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_subclass_')
        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_service_initialization(self):
        """Test Service class initialization"""
        service = Service(pipeline=self.mock_pipeline)

        self.assertIsNotNone(service)
        self.assertIsInstance(service, Pkg)
        self.assertEqual(service.pipeline, self.mock_pipeline)

    def test_application_initialization(self):
        """Test Application class initialization"""
        app = Application(pipeline=self.mock_pipeline)

        self.assertIsNotNone(app)
        self.assertIsInstance(app, Pkg)
        self.assertEqual(app.pipeline, self.mock_pipeline)

    def test_interceptor_initialization(self):
        """Test Interceptor class initialization"""
        interceptor = Interceptor(pipeline=self.mock_pipeline)

        self.assertIsNotNone(interceptor)
        self.assertIsInstance(interceptor, Pkg)
        self.assertEqual(interceptor.pipeline, self.mock_pipeline)

    def test_interceptor_has_modify_env(self):
        """Test Interceptor has modify_env() method"""
        interceptor = Interceptor(pipeline=self.mock_pipeline)

        self.assertTrue(hasattr(interceptor, 'modify_env'))
        self.assertTrue(callable(interceptor.modify_env))

    def test_example_interceptor_modify_env(self):
        """Test example_interceptor's modify_env() implementation"""
        pkg = Pkg.load_standalone('builtin.example_interceptor')
        pkg.configure(library_path='/lib/test.so', custom_env_var='test123')

        pkg.modify_env()

        # Check environment was modified
        self.assertEqual(pkg.env.get('EXAMPLE_INTERCEPTOR_ACTIVE'), 'true')
        self.assertEqual(pkg.env.get('EXAMPLE_CUSTOM_VAR'), 'test123')
        self.assertIn('/lib/test.so', pkg.mod_env.get('LD_PRELOAD', ''))


class TestPkgLifecycleMethods(unittest.TestCase):
    """Test lifecycle methods (start, stop, kill, clean, status)"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_lifecycle_')
        self.mock_pipeline = Mock()
        self.mock_pipeline.name = 'test_pipeline'

        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.shared_dir, exist_ok=True)

        os.environ['JARVIS_CONFIG'] = self.config_dir
        os.environ['JARVIS_PRIVATE'] = self.private_dir
        os.environ['JARVIS_SHARED'] = self.shared_dir

        # Initialize Jarvis properly
        initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if hasattr(Jarvis, '_instance'):
            Jarvis._instance = None

    def test_default_lifecycle_methods_exist(self):
        """Test default lifecycle methods exist and are callable"""
        pkg = Pkg(pipeline=self.mock_pipeline)

        self.assertTrue(hasattr(pkg, 'start'))
        self.assertTrue(hasattr(pkg, 'stop'))
        self.assertTrue(hasattr(pkg, 'kill'))
        self.assertTrue(hasattr(pkg, 'clean'))
        self.assertTrue(hasattr(pkg, 'status'))

        # Should not raise errors
        pkg.start()
        pkg.stop()
        pkg.kill()
        pkg.clean()
        status = pkg.status()

        self.assertEqual(status, "unknown")

    def test_example_app_lifecycle(self):
        """Test example_app implements lifecycle methods correctly"""
        pkg = Pkg.load_standalone('builtin.example_app')
        pkg.configure(message='test message', output_file='test.txt')

        # Start should create marker
        pkg.start()
        start_marker = os.path.join(pkg.shared_dir, 'start.marker')
        self.assertTrue(os.path.exists(start_marker))

        # Stop should create marker
        pkg.stop()
        stop_marker = os.path.join(pkg.shared_dir, 'stop.marker')
        self.assertTrue(os.path.exists(stop_marker))

        # Kill should create marker
        pkg.kill()
        kill_marker = os.path.join(pkg.shared_dir, 'kill.marker')
        self.assertTrue(os.path.exists(kill_marker))

        # Clean should remove all markers
        pkg.clean()
        self.assertFalse(os.path.exists(start_marker))
        self.assertFalse(os.path.exists(stop_marker))
        self.assertFalse(os.path.exists(kill_marker))


if __name__ == '__main__':
    unittest.main()
