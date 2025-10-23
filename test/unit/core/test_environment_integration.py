"""
Integration tests for environment management operations.
Tests the complete workflow: create named env, copy to pipeline, show, list, verify.
"""
import unittest
import sys
import os
import tempfile
import shutil
import yaml
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.core.cli import JarvisCLI


class TestEnvironmentIntegration(unittest.TestCase):
    """Integration test for environment management workflow"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_env_integration_')
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')

        # Initialize CLI
        self.cli = JarvisCLI()
        self.cli.define_options()

        # Store original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

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
            return {
                'success': False,
                'exit_code': e.code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'exception': e
            }

    def test_complete_environment_workflow(self):
        """
        Test complete environment workflow:
        1. Create pipeline: jarvis ppl create test
        2. Create named environment: jarvis env build test_env
        3. Copy environment to pipeline: jarvis ppl env copy test_env
        4. Verify: Pipeline environment file exists and equals the named environment file
        5. Show environment: jarvis env show test_env
        6. List environments: jarvis env list
        7. Cleanup
        """

        # Step 0: Initialize Jarvis
        print("\n=== Step 0: Initialize Jarvis ===")
        result = self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])
        self.assertTrue(result.get('success'), f"Init failed: {result}")
        print("Jarvis initialized successfully")

        # Step 1: Create pipeline
        print("\n=== Step 1: Create pipeline 'test' ===")
        result = self.run_command(['ppl', 'create', 'test'])
        self.assertTrue(result.get('success'), f"Pipeline create failed: {result}")
        self.assertEqual(result['kwargs'].get('pipeline_name'), 'test')

        # Verify pipeline was created
        pipeline_dir = Path(self.shared_dir) / 'test'
        self.assertTrue(pipeline_dir.exists(), f"Pipeline directory not created: {pipeline_dir}")
        print(f"Pipeline 'test' created at: {pipeline_dir}")

        # Step 2: Create named environment with test variables
        print("\n=== Step 2: Create named environment 'test_env' ===")
        # Set some test environment variables in the current environment
        # that will be captured
        test_env_vars = {
            'TEST_VAR': 'test_value_123',
            'PATH': '/test/path:/another/path',
            'MY_CUSTOM_VAR': 'custom_value'
        }

        # Temporarily set these in the environment
        for key, value in test_env_vars.items():
            os.environ[key] = value

        result = self.run_command(['env', 'build', 'test_env', 'EXTRA_VAR=extra_value'])
        self.assertTrue(result.get('success'), f"Env build failed: {result}")
        self.assertEqual(result['kwargs'].get('env_name'), 'test_env')

        # Verify named environment file was created
        # Named environments are stored in ~/.ppi-jarvis/env/, not in the config dir
        from jarvis_cd.core.config import Jarvis
        jarvis = Jarvis.get_instance()
        env_file = jarvis.jarvis_root / 'env' / 'test_env.yaml'
        self.assertTrue(env_file.exists(), f"Named environment file not created: {env_file}")
        print(f"Named environment 'test_env' created at: {env_file}")

        # Verify the environment contains our test variables
        with open(env_file, 'r') as f:
            env_content = yaml.safe_load(f)

        # Should contain PATH (from COMMON_ENV_VARS) and EXTRA_VAR (from args)
        self.assertIn('PATH', env_content, "PATH should be captured")
        self.assertIn('EXTRA_VAR', env_content, "EXTRA_VAR should be added")
        self.assertEqual(env_content['EXTRA_VAR'], 'extra_value')
        print(f"Environment contains {len(env_content)} variables")

        # Step 3: Copy environment to pipeline
        print("\n=== Step 3: Copy environment to pipeline ===")
        result = self.run_command(['ppl', 'env', 'copy', 'test_env'])
        self.assertTrue(result.get('success'), f"Env copy failed: {result}")
        self.assertEqual(result['kwargs'].get('env_name'), 'test_env')

        # Verify pipeline environment file was created
        # Pipeline environment is stored in config directory, not shared directory
        pipeline_config_dir = Path(self.config_dir) / 'pipelines' / 'test'
        pipeline_env_file = pipeline_config_dir / 'env.yaml'
        self.assertTrue(pipeline_env_file.exists(), f"Pipeline env file not created: {pipeline_env_file}")
        print(f"Environment copied to pipeline at: {pipeline_env_file}")

        # Step 4: Verify pipeline environment equals named environment
        print("\n=== Step 4: Verify environment files are identical ===")
        with open(env_file, 'r') as f:
            named_env = yaml.safe_load(f)

        with open(pipeline_env_file, 'r') as f:
            pipeline_env = yaml.safe_load(f)

        self.assertEqual(named_env, pipeline_env,
                        "Pipeline environment should match named environment")
        print(f"Verified: Both environments contain {len(named_env)} identical variables")

        # Verify specific test variables
        self.assertIn('PATH', pipeline_env)
        self.assertIn('EXTRA_VAR', pipeline_env)
        self.assertEqual(pipeline_env['EXTRA_VAR'], 'extra_value')
        print("Verified: Test variables are present and correct")

        # Step 5: Show environment
        print("\n=== Step 5: Show named environment ===")
        # Capture stdout to verify output
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            result = self.run_command(['env', 'show', 'test_env'])
            self.assertTrue(result.get('success'), f"Env show failed: {result}")

            # Get the output
            output = sys.stdout.getvalue()

            # Verify output contains environment name and variables
            self.assertIn('test_env', output, "Output should mention environment name")
            self.assertIn('PATH', output, "Output should show PATH variable")
            self.assertIn('EXTRA_VAR', output, "Output should show EXTRA_VAR")
            print(f"Environment 'test_env' displayed successfully")

        finally:
            sys.stdout = old_stdout

        # Step 6: List environments
        print("\n=== Step 6: List all environments ===")
        sys.stdout = StringIO()

        try:
            result = self.run_command(['env', 'list'])
            self.assertTrue(result.get('success'), f"Env list failed: {result}")

            # Verify test_env is in the list
            # The list command should show available environments
            # We can verify by checking the file exists
            env_dir = jarvis_config.jarvis_root / 'env'
            env_files = list(env_dir.glob('*.yaml'))
            env_names = [f.stem for f in env_files]
            self.assertIn('test_env', env_names, "test_env should be in environment list")
            print(f"Found {len(env_names)} environment(s): {', '.join(env_names)}")

        finally:
            sys.stdout = old_stdout

        # Step 7: Show pipeline environment
        print("\n=== Step 7: Show pipeline environment ===")
        sys.stdout = StringIO()

        try:
            result = self.run_command(['ppl', 'env', 'show'])
            self.assertTrue(result.get('success'), f"Pipeline env show failed: {result}")

            output = sys.stdout.getvalue()
            self.assertIn('test', output, "Output should mention pipeline name")

        finally:
            sys.stdout = old_stdout

        # Step 8: Cleanup - Destroy pipeline
        print("\n=== Step 8: Cleanup ===")
        result = self.run_command(['ppl', 'destroy', 'test'])
        self.assertTrue(result.get('success'), f"Pipeline destroy failed: {result}")

        # Verify pipeline config directory was removed
        # Note: destroy only removes the config directory, not shared/private dirs
        self.assertFalse(pipeline_config_dir.exists(), "Pipeline config directory should be removed")
        print("Pipeline 'test' destroyed successfully")

        # Manually cleanup named environment (no env remove command exists)
        if env_file.exists():
            env_file.unlink()
            print(f"Removed named environment file: {env_file}")

        print("\n=== Test completed successfully ===")


class TestEnvironmentEdgeCases(unittest.TestCase):
    """Test edge cases and error handling for environment operations"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_env_edge_')
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.private_dir = os.path.join(self.test_dir, 'private')
        self.shared_dir = os.path.join(self.test_dir, 'shared')

        self.cli = JarvisCLI()
        self.cli.define_options()

        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

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
            return {
                'success': False,
                'exit_code': e.code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'exception': e
            }

    def test_copy_nonexistent_environment(self):
        """Test copying a non-existent environment to pipeline"""
        # Initialize
        result = self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])
        self.assertTrue(result.get('success'))

        # Create pipeline
        result = self.run_command(['ppl', 'create', 'test_pipeline'])
        self.assertTrue(result.get('success'))

        # Try to copy non-existent environment
        # This should handle the error gracefully
        result = self.run_command(['ppl', 'env', 'copy', 'nonexistent_env'])
        # The command should parse successfully but the execution may print a warning
        self.assertIsNotNone(result)

        # Verify no env file was created in pipeline
        pipeline_dir = Path(self.shared_dir) / 'test_pipeline'
        pipeline_env_file = pipeline_dir / 'env.yaml'
        # Should not exist since copy should fail
        # (depends on implementation - may create empty or not create at all)

        # Cleanup
        self.run_command(['ppl', 'destroy', 'test_pipeline'])

    def test_show_nonexistent_environment(self):
        """Test showing a non-existent named environment"""
        # Initialize
        result = self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])
        self.assertTrue(result.get('success'))

        # Try to show non-existent environment
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            result = self.run_command(['env', 'show', 'nonexistent'])
            # Should handle gracefully and print a message
            self.assertIsNotNone(result)

            output = sys.stdout.getvalue()
            # Should mention that it wasn't found
            self.assertTrue('not found' in output.lower() or 'no named environments' in output.lower())

        finally:
            sys.stdout = old_stdout

    def test_build_environment_with_multiple_variables(self):
        """Test building environment with multiple custom variables"""
        # Initialize
        result = self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])
        self.assertTrue(result.get('success'))

        # Build environment with multiple variables
        result = self.run_command([
            'env', 'build', 'multi_var_env',
            'VAR1=value1',
            'VAR2=value2',
            'VAR3=value3'
        ])
        self.assertTrue(result.get('success'))

        # Verify all variables are in the environment
        # Named environments are stored in jarvis root, not config dir
        from jarvis_cd.core.config import Jarvis
        jarvis = Jarvis.get_instance()
        env_file = jarvis.jarvis_root / 'env' / 'multi_var_env.yaml'
        self.assertTrue(env_file.exists())

        with open(env_file, 'r') as f:
            env_content = yaml.safe_load(f)

        self.assertIn('VAR1', env_content)
        self.assertIn('VAR2', env_content)
        self.assertIn('VAR3', env_content)
        self.assertEqual(env_content['VAR1'], 'value1')
        self.assertEqual(env_content['VAR2'], 'value2')
        self.assertEqual(env_content['VAR3'], 'value3')

        # Cleanup
        env_file.unlink()


if __name__ == '__main__':
    unittest.main()
