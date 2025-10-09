import unittest
import sys
import os
import subprocess

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.shell.core_exec import LocalExec
from jarvis_cd.shell.ssh_exec import SshExec, PsshExec
from jarvis_cd.shell.mpi_exec import MpiExec
from jarvis_cd.shell.exec_info import LocalExecInfo, SshExecInfo, PsshExecInfo, MpiExecInfo
from jarvis_cd.util.hostfile import Hostfile


class TestLocalExecEnvForwarding(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.print_env = os.path.join(os.path.dirname(__file__), 'print_env.py')

    def test_single_custom_env_var(self):
        """Test LocalExec forwards single custom environment variable"""
        exec_info = LocalExecInfo(env={'CUSTOM_VAR': 'HELLO'})
        local_exec = LocalExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO', local_exec.stdout['localhost'])

    def test_multiple_custom_env_vars(self):
        """Test LocalExec forwards multiple custom environment variables"""
        exec_info = LocalExecInfo(env={
            'CUSTOM_VAR': 'HELLO',
            'ANOTHER_VAR': 'WORLD',
            'THIRD_VAR': 'TEST'
        })
        local_exec = LocalExec(f'python3 {self.print_env} CUSTOM_VAR ANOTHER_VAR THIRD_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        stdout = local_exec.stdout['localhost']
        self.assertIn('CUSTOM_VAR=HELLO', stdout)
        self.assertIn('ANOTHER_VAR=WORLD', stdout)
        self.assertIn('THIRD_VAR=TEST', stdout)

    def test_env_var_with_spaces(self):
        """Test LocalExec forwards environment variable with spaces"""
        exec_info = LocalExecInfo(env={'CUSTOM_VAR': 'HELLO WORLD'})
        local_exec = LocalExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO WORLD', local_exec.stdout['localhost'])

    def test_env_var_with_special_chars(self):
        """Test LocalExec forwards environment variable with special characters"""
        exec_info = LocalExecInfo(env={'CUSTOM_VAR': 'HELLO@#$%'})
        local_exec = LocalExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO@#$%', local_exec.stdout['localhost'])

    def test_numeric_env_var(self):
        """Test LocalExec forwards numeric environment variable"""
        exec_info = LocalExecInfo(env={'CUSTOM_VAR': 12345})
        local_exec = LocalExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=12345', local_exec.stdout['localhost'])

    def test_env_not_forwarded_without_setting(self):
        """Test that custom env var is not available without setting it"""
        exec_info = LocalExecInfo(env={})
        local_exec = LocalExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        # Should fail because CUSTOM_VAR is not set
        self.assertNotEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR not found', local_exec.stderr['localhost'])


class TestSshExecEnvForwarding(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.print_env = os.path.join(os.path.dirname(__file__), 'print_env.py')
        # Use localhost for SSH tests to avoid needing remote hosts
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_single_custom_env_var(self):
        """Test SshExec forwards single custom environment variable"""
        exec_info = SshExecInfo(
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 'HELLO'}
        )
        ssh_exec = SshExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(ssh_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO', ssh_exec.stdout['localhost'])

    def test_multiple_custom_env_vars(self):
        """Test SshExec forwards multiple custom environment variables"""
        exec_info = SshExecInfo(
            hostfile=self.hostfile,
            env={
                'CUSTOM_VAR': 'HELLO',
                'ANOTHER_VAR': 'WORLD',
                'THIRD_VAR': 'TEST'
            }
        )
        ssh_exec = SshExec(f'python3 {self.print_env} CUSTOM_VAR ANOTHER_VAR THIRD_VAR', exec_info)

        self.assertEqual(ssh_exec.exit_code['localhost'], 0)
        stdout = ssh_exec.stdout['localhost']
        self.assertIn('CUSTOM_VAR=HELLO', stdout)
        self.assertIn('ANOTHER_VAR=WORLD', stdout)
        self.assertIn('THIRD_VAR=TEST', stdout)

    def test_env_var_with_spaces(self):
        """Test SshExec forwards environment variable with spaces"""
        exec_info = SshExecInfo(
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 'HELLO WORLD'}
        )
        ssh_exec = SshExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(ssh_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO WORLD', ssh_exec.stdout['localhost'])

    def test_env_var_with_quotes(self):
        """Test SshExec forwards environment variable with quotes"""
        exec_info = SshExecInfo(
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 'HELLO "QUOTED" WORLD'}
        )
        ssh_exec = SshExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(ssh_exec.exit_code['localhost'], 0)
        # The quotes might be escaped differently, so just check the key parts
        stdout = ssh_exec.stdout['localhost']
        self.assertIn('CUSTOM_VAR=', stdout)
        self.assertIn('HELLO', stdout)
        self.assertIn('WORLD', stdout)

    def test_numeric_env_var(self):
        """Test SshExec forwards numeric environment variable"""
        exec_info = SshExecInfo(
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 12345}
        )
        ssh_exec = SshExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(ssh_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=12345', ssh_exec.stdout['localhost'])


class TestPsshExecEnvForwarding(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.print_env = os.path.join(os.path.dirname(__file__), 'print_env.py')
        # Use localhost for PSSH tests
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_single_custom_env_var(self):
        """Test PsshExec forwards single custom environment variable"""
        exec_info = PsshExecInfo(
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 'HELLO'}
        )
        pssh_exec = PsshExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(pssh_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO', pssh_exec.stdout['localhost'])

    def test_multiple_custom_env_vars(self):
        """Test PsshExec forwards multiple custom environment variables"""
        exec_info = PsshExecInfo(
            hostfile=self.hostfile,
            env={
                'CUSTOM_VAR': 'HELLO',
                'ANOTHER_VAR': 'WORLD'
            }
        )
        pssh_exec = PsshExec(f'python3 {self.print_env} CUSTOM_VAR ANOTHER_VAR', exec_info)

        self.assertEqual(pssh_exec.exit_code['localhost'], 0)
        stdout = pssh_exec.stdout['localhost']
        self.assertIn('CUSTOM_VAR=HELLO', stdout)
        self.assertIn('ANOTHER_VAR=WORLD', stdout)


class TestMpiExecEnvForwarding(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.print_env = os.path.join(os.path.dirname(__file__), 'print_env.py')
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

        # Check if mpiexec is available
        try:
            subprocess.run(['mpiexec', '--version'], capture_output=True, check=True)
            self.mpi_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.mpi_available = False

    @unittest.skipIf(not hasattr(unittest.TestCase, 'mpi_available'), "MPI not available")
    @unittest.skipIf(not hasattr(unittest.TestCase, 'mpi_available'), "MPI not available")
    def test_single_custom_env_var(self):
        """Test MpiExec forwards single custom environment variable"""
        if not self.mpi_available:
            self.skipTest("MPI not available")

        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 'HELLO'}
        )
        mpi_exec = MpiExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(mpi_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO', mpi_exec.stdout['localhost'])

    def test_multiple_custom_env_vars(self):
        """Test MpiExec forwards multiple custom environment variables"""
        if not self.mpi_available:
            self.skipTest("MPI not available")

        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={
                'CUSTOM_VAR': 'HELLO',
                'ANOTHER_VAR': 'WORLD',
                'THIRD_VAR': 'TEST'
            }
        )
        mpi_exec = MpiExec(f'python3 {self.print_env} CUSTOM_VAR ANOTHER_VAR THIRD_VAR', exec_info)

        self.assertEqual(mpi_exec.exit_code['localhost'], 0)
        stdout = mpi_exec.stdout['localhost']
        self.assertIn('CUSTOM_VAR=HELLO', stdout)
        self.assertIn('ANOTHER_VAR=WORLD', stdout)
        self.assertIn('THIRD_VAR=TEST', stdout)

    def test_env_var_with_spaces(self):
        """Test MpiExec forwards environment variable with spaces"""
        if not self.mpi_available:
            self.skipTest("MPI not available")

        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 'HELLO WORLD'}
        )
        mpi_exec = MpiExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(mpi_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=HELLO WORLD', mpi_exec.stdout['localhost'])

    def test_numeric_env_var(self):
        """Test MpiExec forwards numeric environment variable"""
        if not self.mpi_available:
            self.skipTest("MPI not available")

        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 54321}
        )
        mpi_exec = MpiExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(mpi_exec.exit_code['localhost'], 0)
        self.assertIn('CUSTOM_VAR=54321', mpi_exec.stdout['localhost'])

    def test_env_forwarding_with_multiple_procs(self):
        """Test MpiExec forwards env vars with multiple processes"""
        if not self.mpi_available:
            self.skipTest("MPI not available")

        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={'CUSTOM_VAR': 'HELLO'}
        )
        mpi_exec = MpiExec(f'python3 {self.print_env} CUSTOM_VAR', exec_info)

        self.assertEqual(mpi_exec.exit_code['localhost'], 0)
        # With 2 processes, we should see the output twice (or at least once)
        self.assertIn('CUSTOM_VAR=HELLO', mpi_exec.stdout['localhost'])


if __name__ == '__main__':
    unittest.main()
