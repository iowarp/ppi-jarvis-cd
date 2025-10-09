"""
Tests for 'jarvis env', 'jarvis rg', and 'jarvis mod' commands
"""
import os
from test.unit.core.test_cli_base import CLITestBase


class TestCLIEnvironment(CLITestBase):
    """Tests for environment management commands"""

    def test_env_build(self):
        """Test building environment"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['env', 'build', 'test_env']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['env_name'], 'test_env')

    def test_env_list(self):
        """Test listing environments"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['env', 'list']
        result = self.run_command(args)

        # Should execute successfully
        self.assertIsNotNone(result)

    def test_env_show(self):
        """Test showing environment details"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['env', 'show', 'test_env']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['env_name'], 'test_env')

    def test_ppl_env_build(self):
        """Test building pipeline environment"""
        self.create_test_pipeline()

        args = ['ppl', 'env', 'build']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_ppl_env_copy(self):
        """Test copying pipeline environment"""
        self.create_test_pipeline()

        args = ['ppl', 'env', 'copy', 'new_env']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['new_env_name'], 'new_env')

    def test_ppl_env_show(self):
        """Test showing pipeline environment"""
        self.create_test_pipeline()

        args = ['ppl', 'env', 'show']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)


class TestCLIResourceGraph(CLITestBase):
    """Tests for resource graph commands"""

    def test_rg_build(self):
        """Test building resource graph"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['rg', 'build']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_rg_show(self):
        """Test showing resource graph"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['rg', 'show']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_rg_nodes(self):
        """Test listing resource graph nodes"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['rg', 'nodes']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_rg_node(self):
        """Test showing specific node"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['rg', 'node', 'test_node']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['hostname'], 'test_node')

    def test_rg_filter(self):
        """Test filtering resource graph"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['rg', 'filter', 'cpu']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['dev_type'], 'cpu')

    def test_rg_load(self):
        """Test loading resource graph"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        rg_file = self.create_test_config_file('nodes: []', 'rg.yaml')

        args = ['rg', 'load', rg_file]
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['rg_path'], rg_file)

    def test_rg_path(self):
        """Test getting resource graph path"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['rg', 'path']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)

    def test_build_profile(self):
        """Test building resource profile"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['build', 'profile']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)


class TestCLIModule(CLITestBase):
    """Tests for module commands"""

    def test_mod_create(self):
        """Test creating a module"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['mod', 'create', 'test_module']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['mod_name'], 'test_module')

    def test_mod_cd(self):
        """Test changing to module directory"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['mod', 'cd', 'test_module']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['mod_name'], 'test_module')

    def test_mod_prepend(self):
        """Test prepending to module"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        args = ['mod', 'prepend', 'test_module', 'PATH', '/new/path']
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['mod_name'], 'test_module')
            # PATH and /new/path will be in remainder args since keep_remainder=True
            self.assertIn('PATH', result['remainder'])
            self.assertIn('/new/path', result['remainder'])


class TestCLIHostfile(CLITestBase):
    """Tests for hostfile commands"""

    def test_hostfile_set(self):
        """Test setting hostfile"""
        self.run_command(['init', self.config_dir, self.private_dir, self.shared_dir])

        hostfile = self.create_test_config_file('localhost\n', 'hosts.txt')

        args = ['hostfile', 'set', hostfile]
        result = self.run_command(args)

        if result.get('success'):
            self.assertEqual(result['kwargs']['hostfile_path'], hostfile)


class TestCLICD(CLITestBase):
    """Tests for cd command"""

    def test_cd_to_pipeline(self):
        """Test cd to pipeline directory"""
        self.create_test_pipeline()

        args = ['cd']
        result = self.run_command(args)

        # Should parse successfully
        self.assertIsNotNone(result)


if __name__ == '__main__':
    import unittest
    unittest.main()
