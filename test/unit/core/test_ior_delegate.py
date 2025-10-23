"""
Unit tests for IOR package delegation functionality.
Tests the _get_delegate method in the Pkg base class.
"""
import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.core.config import Jarvis
from jarvis_cd.core.pipeline import Pipeline


def initialize_jarvis_for_test(config_dir, private_dir, shared_dir):
    """Helper function to properly initialize Jarvis for testing"""
    # Get Jarvis singleton and initialize it
    jarvis = Jarvis.get_instance()
    jarvis.initialize(config_dir, private_dir, shared_dir, force=True)

    return jarvis


class TestIorDelegation(unittest.TestCase):
    """Test the IOR package delegation functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_ior_delegate_')
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
        self.jarvis = initialize_jarvis_for_test(self.config_dir, self.private_dir, self.shared_dir)

        # Create a test pipeline
        self.pipeline = Pipeline()
        self.pipeline.create('test_ior_pipeline')

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_delegate_default_mode(self):
        """Test delegation to IorDefault implementation"""
        # Create package definition directly to avoid validation
        pkg_def = {
            'pkg_type': 'builtin.ior',
            'pkg_id': 'test_ior',
            'pkg_name': 'ior',
            'global_id': f'{self.pipeline.name}.test_ior',
            'config': {
                'deploy_mode': 'default',
                'nprocs': 1,
                'ppn': 16,
                'block': '32m',
                'xfer': '1m',
                'api': 'posix',
                'out': '/tmp/ior.bin',
                'log': '/tmp/ior.log',
                'write': True,
                'read': False,
                'fpp': False,
                'reps': 1,
                'direct': False,
                'interceptors': []
            }
        }
        self.pipeline.packages.append(pkg_def)
        self.pipeline.save()

        # Find the package in pipeline
        pkg_def = None
        for pkg in self.pipeline.packages:
            if pkg['pkg_id'] == 'test_ior':
                pkg_def = pkg
                break

        self.assertIsNotNone(pkg_def, "IOR package should be in pipeline")

        # Load the package instance
        from jarvis_cd.core.pipeline import Pipeline
        pkg_instance = self.pipeline._load_package_instance(pkg_def, {})

        # Configure with default deploy mode
        pkg_instance.configure(deploy_mode='default')

        # Get delegate for default mode
        delegate = pkg_instance._get_delegate('default')

        # Verify delegate is IorDefault
        self.assertEqual(delegate.__class__.__name__, 'IorDefault',
                        "Delegate should be IorDefault for deploy='default'")

        # Verify delegate has same config
        self.assertEqual(delegate.config.get('deploy_mode'), 'default',
                        "Delegate should have same config")

    def test_delegate_container_mode(self):
        """Test delegation to IorContainer implementation"""
        # Create package definition directly
        pkg_def = {
            'pkg_type': 'builtin.ior',
            'pkg_id': 'test_ior',
            'pkg_name': 'ior',
            'global_id': f'{self.pipeline.name}.test_ior',
            'config': {
                'deploy_mode': 'container',
                'nprocs': 1,
                'ppn': 16,
                'block': '32m',
                'xfer': '1m',
                'api': 'posix',
                'out': '/tmp/ior.bin',
                'log': '/tmp/ior.log',
                'write': True,
                'read': False,
                'fpp': False,
                'reps': 1,
                'direct': False,
                'interceptors': []
            }
        }
        self.pipeline.packages.append(pkg_def)
        self.pipeline.save()

        # Find the package in pipeline
        pkg_def = None
        for pkg in self.pipeline.packages:
            if pkg['pkg_id'] == 'test_ior':
                pkg_def = pkg
                break

        self.assertIsNotNone(pkg_def, "IOR package should be in pipeline")

        # Load the package instance
        pkg_instance = self.pipeline._load_package_instance(pkg_def, {})

        # Configure with container deploy mode
        pkg_instance.configure(deploy_mode='container')

        # Get delegate for container mode
        delegate = pkg_instance._get_delegate('container')

        # Verify delegate is IorContainer
        self.assertEqual(delegate.__class__.__name__, 'IorContainer',
                        "Delegate should be IorContainer for deploy_mode='container'")

        # Verify delegate has same config
        self.assertEqual(delegate.config.get('deploy_mode'), 'container',
                        "Delegate should have same config")

    def test_delegate_caching(self):
        """Test that delegates are cached properly"""
        # Create package definition directly
        pkg_def = {
            'pkg_type': 'builtin.ior',
            'pkg_id': 'test_ior',
            'pkg_name': 'ior',
            'global_id': f'{self.pipeline.name}.test_ior',
            'config': {
                'deploy_mode': 'default',
                'nprocs': 1,
                'ppn': 16,
                'block': '32m',
                'xfer': '1m',
                'api': 'posix',
                'out': '/tmp/ior.bin',
                'log': '/tmp/ior.log',
                'write': True,
                'read': False,
                'fpp': False,
                'reps': 1,
                'direct': False,
                'interceptors': []
            }
        }
        self.pipeline.packages.append(pkg_def)
        self.pipeline.save()

        # Find the package in pipeline
        pkg_def = None
        for pkg in self.pipeline.packages:
            if pkg['pkg_id'] == 'test_ior':
                pkg_def = pkg
                break

        self.assertIsNotNone(pkg_def, "IOR package should be in pipeline")

        # Load the package instance
        pkg_instance = self.pipeline._load_package_instance(pkg_def, {})

        # Configure with default deploy mode
        pkg_instance.configure(deploy_mode='default')

        # Get delegate twice
        delegate1 = pkg_instance._get_delegate('default')
        delegate2 = pkg_instance._get_delegate('default')

        # Verify they are the same instance (cached)
        self.assertIs(delegate1, delegate2,
                     "Delegate should be cached and return same instance")

    def test_delegate_multiple_modes(self):
        """Test that different deploy modes create different delegates"""
        # Create package definition directly
        pkg_def = {
            'pkg_type': 'builtin.ior',
            'pkg_id': 'test_ior',
            'pkg_name': 'ior',
            'global_id': f'{self.pipeline.name}.test_ior',
            'config': {
                'deploy_mode': 'default',
                'nprocs': 1,
                'ppn': 16,
                'block': '32m',
                'xfer': '1m',
                'api': 'posix',
                'out': '/tmp/ior.bin',
                'log': '/tmp/ior.log',
                'write': True,
                'read': False,
                'fpp': False,
                'reps': 1,
                'direct': False,
                'interceptors': []
            }
        }
        self.pipeline.packages.append(pkg_def)
        self.pipeline.save()

        # Find the package in pipeline
        pkg_def = None
        for pkg in self.pipeline.packages:
            if pkg['pkg_id'] == 'test_ior':
                pkg_def = pkg
                break

        self.assertIsNotNone(pkg_def, "IOR package should be in pipeline")

        # Load the package instance
        pkg_instance = self.pipeline._load_package_instance(pkg_def, {})

        # Configure
        pkg_instance.configure(deploy_mode='default')

        # Get delegates for different modes
        delegate_default = pkg_instance._get_delegate('default')
        delegate_container = pkg_instance._get_delegate('container')

        # Verify they are different instances
        self.assertIsNot(delegate_default, delegate_container,
                        "Different deploy modes should create different delegates")

        # Verify correct types
        self.assertEqual(delegate_default.__class__.__name__, 'IorDefault')
        self.assertEqual(delegate_container.__class__.__name__, 'IorContainer')

    def test_delegate_invalid_mode(self):
        """Test that invalid deploy mode raises proper error"""
        # Create package definition directly
        pkg_def = {
            'pkg_type': 'builtin.ior',
            'pkg_id': 'test_ior',
            'pkg_name': 'ior',
            'global_id': f'{self.pipeline.name}.test_ior',
            'config': {
                'deploy_mode': 'default',
                'nprocs': 1,
                'ppn': 16,
                'block': '32m',
                'xfer': '1m',
                'api': 'posix',
                'out': '/tmp/ior.bin',
                'log': '/tmp/ior.log',
                'write': True,
                'read': False,
                'fpp': False,
                'reps': 1,
                'direct': False,
                'interceptors': []
            }
        }
        self.pipeline.packages.append(pkg_def)
        self.pipeline.save()

        # Find the package in pipeline
        pkg_def = None
        for pkg in self.pipeline.packages:
            if pkg['pkg_id'] == 'test_ior':
                pkg_def = pkg
                break

        self.assertIsNotNone(pkg_def, "IOR package should be in pipeline")

        # Load the package instance
        pkg_instance = self.pipeline._load_package_instance(pkg_def, {})

        # Configure
        pkg_instance.configure(deploy_mode='default')

        # Try to get delegate with invalid mode
        with self.assertRaises(ImportError) as context:
            pkg_instance._get_delegate('invalid_mode')

        self.assertIn('invalid_mode', str(context.exception),
                     "Error should mention the invalid mode")

    def test_delegate_state_sharing(self):
        """Test that delegate shares state with parent"""
        # Create package definition directly
        pkg_def = {
            'pkg_type': 'builtin.ior',
            'pkg_id': 'test_ior',
            'pkg_name': 'ior',
            'global_id': f'{self.pipeline.name}.test_ior',
            'config': {
                'deploy_mode': 'default',
                'nprocs': 4,
                'ppn': 16,
                'block': '64m',
                'xfer': '1m',
                'api': 'posix',
                'out': '/tmp/ior.bin',
                'log': '/tmp/ior.log',
                'write': True,
                'read': False,
                'fpp': False,
                'reps': 1,
                'direct': False,
                'interceptors': []
            }
        }
        self.pipeline.packages.append(pkg_def)
        self.pipeline.save()

        # Find the package in pipeline
        pkg_def = None
        for pkg in self.pipeline.packages:
            if pkg['pkg_id'] == 'test_ior':
                pkg_def = pkg
                break

        self.assertIsNotNone(pkg_def, "IOR package should be in pipeline")

        # Load the package instance
        pkg_instance = self.pipeline._load_package_instance(pkg_def, {})

        # Configure
        pkg_instance.configure(deploy_mode='default', nprocs=4, block='64m')

        # Get delegate
        delegate = pkg_instance._get_delegate('default')

        # Verify delegate has same pkg_id, global_id, and config
        self.assertEqual(delegate.pkg_id, pkg_instance.pkg_id,
                        "Delegate should have same pkg_id")
        self.assertEqual(delegate.global_id, pkg_instance.global_id,
                        "Delegate should have same global_id")
        self.assertEqual(delegate.config.get('nprocs'), 4,
                        "Delegate should have same config values")
        self.assertEqual(delegate.config.get('block'), '64m',
                        "Delegate should have same config values")


if __name__ == '__main__':
    unittest.main()
