import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.shell.ssh_exec import SshExec, PsshExec
from jarvis_cd.shell.exec_info import SshExecInfo, PsshExecInfo
from jarvis_cd.util.hostfile import Hostfile


class TestSshExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_binary = os.path.join(os.path.dirname(__file__), 'test_env_checker')
        self.hostfile = Hostfile(hosts=['testhost'], find_ips=False)

    def test_basic_ssh_command(self):
        """Test basic SSH command construction"""
        exec_info = SshExecInfo(hostfile=self.hostfile, exec_async=True)
        ssh_exec = SshExec('echo "hello"', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('ssh', cmd)
        self.assertIn('testhost', cmd)
        self.assertIn('echo "hello"', cmd)

    def test_ssh_with_user(self):
        """Test SSH command with user"""
        exec_info = SshExecInfo(
            user='testuser',
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo "test"', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('testuser@testhost', cmd)

    def test_ssh_with_port(self):
        """Test SSH command with custom port"""
        exec_info = SshExecInfo(
            port=2222,
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo "test"', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('-p 2222', cmd)

    def test_ssh_with_pkey(self):
        """Test SSH command with private key"""
        exec_info = SshExecInfo(
            pkey='/path/to/key.pem',
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo "test"', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('-i /path/to/key.pem', cmd)

    def test_ssh_strict_mode(self):
        """Test SSH with strict host key checking"""
        exec_info = SshExecInfo(
            strict_ssh=True,
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo "test"', exec_info)

        cmd = ssh_exec.get_cmd()
        # Should NOT contain StrictHostKeyChecking=no
        self.assertNotIn('StrictHostKeyChecking=no', cmd)

    def test_ssh_non_strict_mode(self):
        """Test SSH with non-strict host key checking"""
        exec_info = SshExecInfo(
            strict_ssh=False,
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo "test"', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('StrictHostKeyChecking=no', cmd)

    def test_ssh_with_single_env_variable(self):
        """Test SSH command with single environment variable"""
        exec_info = SshExecInfo(
            env={'TEST_VAR': 'test_value'},
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec(self.test_binary + ' TEST_VAR', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('TEST_VAR', cmd)
        self.assertIn('test_value', cmd)

    def test_ssh_with_multiple_env_variables(self):
        """Test SSH command with multiple environment variables"""
        exec_info = SshExecInfo(
            env={
                'VAR1': 'value1',
                'VAR2': 'value2',
                'VAR3': 'value3'
            },
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec(self.test_binary + ' VAR1 VAR2 VAR3', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('VAR1', cmd)
        self.assertIn('value1', cmd)
        self.assertIn('VAR2', cmd)
        self.assertIn('value2', cmd)
        self.assertIn('VAR3', cmd)
        self.assertIn('value3', cmd)

    def test_ssh_env_with_special_characters(self):
        """Test SSH environment variables with special characters"""
        exec_info = SshExecInfo(
            env={'SPECIAL_VAR': "value with 'quotes'"},
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo $SPECIAL_VAR', exec_info)

        cmd = ssh_exec.get_cmd()
        # Should properly escape quotes
        self.assertIn('SPECIAL_VAR', cmd)

    def test_ssh_with_cwd(self):
        """Test SSH command with working directory change"""
        exec_info = SshExecInfo(
            cwd='/tmp/test',
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('pwd', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('cd /tmp/test', cmd)

    def test_ssh_with_sudo(self):
        """Test SSH command with sudo"""
        exec_info = SshExecInfo(
            sudo=True,
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('whoami', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('sudo', cmd)

    def test_ssh_with_sudo_and_env(self):
        """Test SSH command with sudo preserving environment"""
        exec_info = SshExecInfo(
            sudo=True,
            sudoenv=True,
            env={'TEST_VAR': 'value'},
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo $TEST_VAR', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('sudo -E', cmd)
        self.assertIn('TEST_VAR', cmd)

    def test_ssh_with_sudo_no_env(self):
        """Test SSH command with sudo not preserving environment"""
        exec_info = SshExecInfo(
            sudo=True,
            sudoenv=False,
            env={'TEST_VAR': 'value'},
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo $TEST_VAR', exec_info)

        cmd = ssh_exec.get_cmd()
        # Should have 'sudo' but not 'sudo -E'
        self.assertIn('sudo', cmd)
        self.assertNotIn('sudo -E', cmd)

    def test_ssh_with_timeout(self):
        """Test SSH command with connection timeout"""
        exec_info = SshExecInfo(
            timeout=30,
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo "test"', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('ConnectTimeout=30', cmd)

    def test_ssh_hostname_override(self):
        """Test SSH execution with explicit hostname override"""
        multi_host = Hostfile(hosts=['host1', 'host2'], find_ips=False)
        exec_info = SshExecInfo(hostfile=multi_host, exec_async=True)
        ssh_exec = SshExec('echo "test"', exec_info, hostname='host2')

        cmd = ssh_exec.get_cmd()
        self.assertIn('host2', cmd)
        self.assertNotIn('host1', cmd)

    def test_ssh_env_numeric_values(self):
        """Test SSH environment variables with numeric values"""
        exec_info = SshExecInfo(
            env={
                'INT_VAR': 42,
                'FLOAT_VAR': 3.14
            },
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec(self.test_binary + ' INT_VAR FLOAT_VAR', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('INT_VAR', cmd)
        self.assertIn('42', cmd)
        self.assertIn('FLOAT_VAR', cmd)
        self.assertIn('3.14', cmd)

    def test_ssh_combined_options(self):
        """Test SSH with multiple options combined"""
        exec_info = SshExecInfo(
            user='testuser',
            port=2222,
            pkey='/path/to/key',
            cwd='/tmp',
            env={'VAR1': 'value1', 'VAR2': 'value2'},
            sudo=True,
            sudoenv=True,
            hostfile=self.hostfile,
            exec_async=True
        )
        ssh_exec = SshExec('echo "test"', exec_info)

        cmd = ssh_exec.get_cmd()
        self.assertIn('testuser@testhost', cmd)
        self.assertIn('-p 2222', cmd)
        self.assertIn('-i /path/to/key', cmd)
        self.assertIn('cd /tmp', cmd)
        self.assertIn('VAR1', cmd)
        self.assertIn('VAR2', cmd)
        self.assertIn('sudo -E', cmd)


class TestPsshExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_binary = os.path.join(os.path.dirname(__file__), 'test_env_checker')
        self.multi_host = Hostfile(hosts=['host1', 'host2', 'host3'], find_ips=False)

    def test_pssh_requires_hostfile(self):
        """Test that PSSH requires a hostfile"""
        exec_info = PsshExecInfo(hostfile=None, exec_async=True)

        with self.assertRaises(ValueError):
            PsshExec('echo "test"', exec_info)

    def test_pssh_empty_hostfile(self):
        """Test that PSSH requires non-empty hostfile"""
        empty_hostfile = Hostfile(hosts=[], find_ips=False)
        exec_info = PsshExecInfo(hostfile=empty_hostfile, exec_async=True)

        with self.assertRaises(ValueError):
            PsshExec('echo "test"', exec_info)

    @patch('jarvis_cd.shell.ssh_exec.SshExec')
    def test_pssh_creates_ssh_for_each_host(self, mock_ssh_exec):
        """Test that PSSH creates SSH executor for each host"""
        exec_info = PsshExecInfo(hostfile=self.multi_host, exec_async=True)

        # Mock SshExec to avoid actual execution
        mock_instances = []
        for i in range(3):
            mock_instance = MagicMock()
            mock_instance.processes = {f'host{i+1}': MagicMock()}
            mock_instances.append(mock_instance)

        mock_ssh_exec.side_effect = mock_instances

        pssh_exec = PsshExec('echo "test"', exec_info)

        # Should create 3 SSH executors, one for each host
        self.assertEqual(mock_ssh_exec.call_count, 3)

    @patch('jarvis_cd.shell.ssh_exec.SshExec')
    def test_pssh_env_forwarding(self, mock_ssh_exec):
        """Test that PSSH forwards environment variables to SSH executors"""
        exec_info = PsshExecInfo(
            env={'TEST_VAR': 'test_value'},
            hostfile=self.multi_host,
            exec_async=True
        )

        # Mock SshExec
        mock_instance = MagicMock()
        mock_instance.processes = {'host1': MagicMock()}
        mock_ssh_exec.return_value = mock_instance

        pssh_exec = PsshExec('echo $TEST_VAR', exec_info)

        # Check that environment was passed to SSH executors
        for call in mock_ssh_exec.call_args_list:
            ssh_info = call[0][1]
            self.assertIn('TEST_VAR', ssh_info.env)
            self.assertEqual(ssh_info.env['TEST_VAR'], 'test_value')

    @patch('jarvis_cd.shell.ssh_exec.SshExec')
    def test_pssh_parallel_execution(self, mock_ssh_exec):
        """Test that PSSH executes on all hosts in parallel"""
        exec_info = PsshExecInfo(hostfile=self.multi_host, exec_async=True)

        # Create mock instances for each host
        mock_instances = []
        for hostname in self.multi_host.hosts:
            mock_instance = MagicMock()
            mock_instance.processes = {hostname: MagicMock()}
            mock_instances.append(mock_instance)

        mock_ssh_exec.side_effect = mock_instances

        pssh_exec = PsshExec('echo "test"', exec_info)

        # Verify SSH was created for each host with correct hostname
        self.assertEqual(mock_ssh_exec.call_count, 3)

        # Extract hostnames from call args (positional arg 2 or keyword arg 'hostname')
        call_hostnames = []
        for call in mock_ssh_exec.call_args_list:
            args, kwargs = call
            if 'hostname' in kwargs:
                call_hostnames.append(kwargs['hostname'])
            elif len(args) > 2:
                call_hostnames.append(args[2])

        self.assertIn('host1', call_hostnames)
        self.assertIn('host2', call_hostnames)
        self.assertIn('host3', call_hostnames)

    def test_pssh_get_cmd(self):
        """Test that PSSH get_cmd returns original command"""
        exec_info = PsshExecInfo(hostfile=self.multi_host, exec_async=True)

        with patch('jarvis_cd.shell.ssh_exec.SshExec'):
            pssh_exec = PsshExec('echo "test"', exec_info)
            self.assertEqual(pssh_exec.get_cmd(), 'echo "test"')


if __name__ == '__main__':
    unittest.main()
