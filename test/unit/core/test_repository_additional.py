"""
Additional repository manager tests for improved coverage
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.core.repository import RepositoryManager
from jarvis_cd.core.config import Jarvis


class TestRepositoryManagerAdditional(unittest.TestCase):
    """Additional tests for RepositoryManager"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.test_dir / 'config'
        self.private_dir = self.test_dir / 'private'
        self.shared_dir = self.test_dir / 'shared'
        self.jarvis_root = self.test_dir / '.ppi-jarvis'

        # Reset and initialize Jarvis singleton
        Jarvis._instance = None
        self.jarvis_config = Jarvis(jarvis_root=str(self.jarvis_root))
        self.jarvis_config.initialize(
            str(self.config_dir),
            str(self.private_dir),
            str(self.shared_dir)
        )

        self.repo_manager = RepositoryManager(self.jarvis_config)

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_add_repository_not_exists(self):
        """Test adding a repository that doesn't exist"""
        fake_path = self.test_dir / 'nonexistent_repo'

        with self.assertRaises(FileNotFoundError) as context:
            self.repo_manager.add_repository(str(fake_path))

        self.assertIn('does not exist', str(context.exception))

    def test_add_repository_not_directory(self):
        """Test adding a repository that is a file, not a directory"""
        file_path = self.test_dir / 'test_file.txt'
        file_path.write_text('test')

        with self.assertRaises(ValueError) as context:
            self.repo_manager.add_repository(str(file_path))

        self.assertIn('not a directory', str(context.exception))

    def test_add_repository_invalid_structure(self):
        """Test adding a repository with invalid structure"""
        repo_dir = self.test_dir / 'bad_repo'
        repo_dir.mkdir()

        # Missing the required subdirectory with same name
        with self.assertRaises(ValueError) as context:
            self.repo_manager.add_repository(str(repo_dir))

        self.assertIn('Invalid repository structure', str(context.exception))
        self.assertIn('does not contain subdirectory', str(context.exception))

    def test_add_repository_subdirectory_is_file(self):
        """Test adding a repository where expected subdirectory is actually a file"""
        repo_dir = self.test_dir / 'file_repo'
        repo_dir.mkdir()

        # Create a file instead of directory
        (repo_dir / 'file_repo').write_text('not a directory')

        with self.assertRaises(ValueError) as context:
            self.repo_manager.add_repository(str(repo_dir))

        self.assertIn('not a directory', str(context.exception))

    def test_add_repository_valid(self):
        """Test adding a valid repository"""
        repo_dir = self.test_dir / 'valid_repo'
        repo_subdir = repo_dir / 'valid_repo'
        repo_subdir.mkdir(parents=True)

        # Should succeed
        self.repo_manager.add_repository(str(repo_dir))

        # Verify it's in the config
        self.assertIn(str(repo_dir.absolute()), self.jarvis_config.repos['repos'])

    def test_remove_repository_by_name(self):
        """Test removing repository by name"""
        # Create and add a repository
        repo_dir = self.test_dir / 'test_repo'
        repo_subdir = repo_dir / 'test_repo'
        repo_subdir.mkdir(parents=True)

        self.repo_manager.add_repository(str(repo_dir))

        # Remove by name
        removed_count = self.repo_manager.remove_repository_by_name('test_repo')

        self.assertEqual(removed_count, 1)
        self.assertNotIn(str(repo_dir.absolute()), self.jarvis_config.repos['repos'])

    def test_create_package_invalid_type(self):
        """Test creating package with invalid type"""
        with self.assertRaises(ValueError) as context:
            self.repo_manager.create_package('test_pkg', 'invalid_type')

        self.assertIn('Invalid package type', str(context.exception))
        self.assertIn('service, app, or interceptor', str(context.exception))

    def test_create_package_no_repos(self):
        """Test creating package when no repositories are registered"""
        # Clear all repos including builtin
        self.jarvis_config.repos['repos'] = []

        with self.assertRaises(ValueError) as context:
            self.repo_manager.create_package('test_pkg', 'app')

        self.assertIn('No repositories registered', str(context.exception))

    def test_create_package_repo_not_exists(self):
        """Test creating package when repository doesn't exist"""
        # Clear all repos and add only a non-existent repo
        fake_repo = self.test_dir / 'fake_repo'
        self.jarvis_config.repos['repos'] = [str(fake_repo)]

        with self.assertRaises(FileNotFoundError) as context:
            self.repo_manager.create_package('test_pkg', 'app')

        self.assertIn('does not exist', str(context.exception))

    def test_create_package_service(self):
        """Test creating a service package"""
        # Create and add a repository
        repo_dir = self.test_dir / 'test_repo'
        repo_subdir = repo_dir / 'test_repo'
        repo_subdir.mkdir(parents=True)
        self.repo_manager.add_repository(str(repo_dir))

        # Create service package
        self.repo_manager.create_package('my_service', 'service')

        # Verify package file was created
        package_file = repo_subdir / 'my_service' / 'package.py'
        self.assertTrue(package_file.exists())

        # Verify content has Service base class
        content = package_file.read_text()
        self.assertIn('from jarvis_cd.core.pkg import Service', content)
        self.assertIn('class My_service(Service):', content)
        self.assertIn('def start(self):', content)
        self.assertIn('def stop(self):', content)

    def test_create_package_app(self):
        """Test creating an application package"""
        repo_dir = self.test_dir / 'test_repo'
        repo_subdir = repo_dir / 'test_repo'
        repo_subdir.mkdir(parents=True)
        self.repo_manager.add_repository(str(repo_dir))

        # Create app package
        self.repo_manager.create_package('my_app', 'app')

        # Verify package file was created
        package_file = repo_subdir / 'my_app' / 'package.py'
        self.assertTrue(package_file.exists())

        # Verify content has Application base class
        content = package_file.read_text()
        self.assertIn('from jarvis_cd.core.pkg import Application', content)
        self.assertIn('class My_app(Application):', content)
        self.assertIn('def _prepare_input(self):', content)

    def test_create_package_interceptor(self):
        """Test creating an interceptor package"""
        repo_dir = self.test_dir / 'test_repo'
        repo_subdir = repo_dir / 'test_repo'
        repo_subdir.mkdir(parents=True)
        self.repo_manager.add_repository(str(repo_dir))

        # Create interceptor package
        self.repo_manager.create_package('my_interceptor', 'interceptor')

        # Verify package file was created
        package_file = repo_subdir / 'my_interceptor' / 'package.py'
        self.assertTrue(package_file.exists())

        # Verify content has Interceptor base class
        content = package_file.read_text()
        self.assertIn('from jarvis_cd.core.pkg import Interceptor', content)
        self.assertIn('class My_interceptor(Interceptor):', content)
        self.assertIn('def modify_env(self):', content)
        self.assertIn('LD_PRELOAD', content)

    def test_list_packages_in_repo_empty(self):
        """Test listing packages in empty repository"""
        repo_dir = self.test_dir / 'empty_repo'
        repo_subdir = repo_dir / 'empty_repo'
        repo_subdir.mkdir(parents=True)

        packages = self.repo_manager.list_packages_in_repo(str(repo_dir))

        self.assertEqual(packages, [])

    def test_list_packages_in_repo_nonexistent(self):
        """Test listing packages in nonexistent repository"""
        fake_repo = self.test_dir / 'fake_repo'

        packages = self.repo_manager.list_packages_in_repo(str(fake_repo))

        self.assertEqual(packages, [])

    def test_list_packages_in_repo_with_packages(self):
        """Test listing packages in repository with packages"""
        repo_dir = self.test_dir / 'pkg_repo'
        repo_subdir = repo_dir / 'pkg_repo'
        repo_subdir.mkdir(parents=True)

        # Create some package directories
        pkg1_dir = repo_subdir / 'package1'
        pkg1_dir.mkdir()
        (pkg1_dir / 'package.py').write_text('# Package 1')

        pkg2_dir = repo_subdir / 'package2'
        pkg2_dir.mkdir()
        (pkg2_dir / 'package.py').write_text('# Package 2')

        # Create a directory without package.py (should be ignored)
        not_pkg_dir = repo_subdir / 'not_a_package'
        not_pkg_dir.mkdir()

        packages = self.repo_manager.list_packages_in_repo(str(repo_dir))

        self.assertEqual(sorted(packages), ['package1', 'package2'])

    def test_find_all_packages(self):
        """Test finding all packages across repositories"""
        # Create builtin-like structure
        builtin_dir = self.jarvis_config.get_builtin_repo_path()
        builtin_subdir = builtin_dir / 'builtin'
        builtin_subdir.mkdir(parents=True, exist_ok=True)

        # Add a builtin package
        builtin_pkg = builtin_subdir / 'builtin_pkg'
        builtin_pkg.mkdir(exist_ok=True)
        (builtin_pkg / 'package.py').write_text('# Builtin')

        # Create custom repo
        custom_dir = self.test_dir / 'custom_repo'
        custom_subdir = custom_dir / 'custom_repo'
        custom_subdir.mkdir(parents=True)

        custom_pkg = custom_subdir / 'custom_pkg'
        custom_pkg.mkdir()
        (custom_pkg / 'package.py').write_text('# Custom')

        self.repo_manager.add_repository(str(custom_dir))

        # Find all packages
        all_packages = self.repo_manager.find_all_packages()

        # Should have both repos
        self.assertIn('builtin', all_packages)
        self.assertIn('custom_repo', all_packages)

        # Check package lists
        self.assertIn('builtin_pkg', all_packages['builtin'])
        self.assertIn('custom_pkg', all_packages['custom_repo'])


if __name__ == '__main__':
    unittest.main()
