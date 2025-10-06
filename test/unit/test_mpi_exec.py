import unittest
import sys
import os

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.shell.mpi_exec import MpiExec, OpenMpiExec, MpichExec, CrayMpichExec
from jarvis_cd.shell.exec_info import MpiExecInfo
from jarvis_cd.util.hostfile import Hostfile


class TestMpiExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_single_command_format(self):
        """Test MPI execution with a single command string"""
        exec_info = MpiExecInfo(
            nprocs=4,
            ppn=2,
            hostfile=self.hostfile,
            env={'TEST_VAR': 'test_value'}
        )

        mpi_exec = MpiExec('echo "hello world"', exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify basic command structure
        self.assertIn('mpiexec', cmd)
        self.assertIn('echo "hello world"', cmd)

    def test_multi_command_format(self):
        """Test MPI execution with multiple commands"""
        exec_info = MpiExecInfo(
            nprocs=10,
            hostfile=self.hostfile
        )

        cmd_list = [
            {'cmd': 'gdbserver :1234 ./myapp', 'nprocs': 1},
            {'cmd': './myapp', 'nprocs': None}  # Should get remaining 9 procs
        ]

        mpi_exec = MpiExec(cmd_list, exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify multi-command structure
        self.assertIn('mpiexec', cmd)
        self.assertIn('gdbserver', cmd)
        self.assertIn('./myapp', cmd)

    def test_multi_command_with_zero_nprocs(self):
        """Test that commands with 0 nprocs are skipped"""
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=self.hostfile
        )

        cmd_list = [
            {'cmd': 'gdbserver :1234 ./myapp', 'nprocs': 0},  # Should be skipped
            {'cmd': './myapp', 'nprocs': None}  # Should get all 4 procs
        ]

        mpi_exec = MpiExec(cmd_list, exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify gdbserver command is not included
        self.assertNotIn('gdbserver', cmd)
        self.assertIn('./myapp', cmd)

    def test_environment_variables(self):
        """Test that environment variables are properly forwarded"""
        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={'MY_VAR': 'my_value', 'ANOTHER_VAR': 'another_value'}
        )

        mpi_exec = MpiExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify environment variables are in the command
        # The exact format depends on MPI implementation
        self.assertTrue(
            'MY_VAR' in cmd or 'ANOTHER_VAR' in cmd,
            "Environment variables should be included in MPI command"
        )

    def test_ppn_option(self):
        """Test processes per node option"""
        exec_info = MpiExecInfo(
            nprocs=8,
            ppn=4,
            hostfile=self.hostfile
        )

        mpi_exec = MpiExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify ppn option is included (format varies by MPI)
        self.assertTrue(
            'ppn' in cmd or 'npernode' in cmd,
            "PPN option should be in MPI command"
        )

    def test_hostfile_option(self):
        """Test hostfile option with multiple hosts"""
        multi_host = Hostfile(hosts=['host1', 'host2', 'host3'], find_ips=False)
        exec_info = MpiExecInfo(
            nprocs=6,
            hostfile=multi_host
        )

        mpi_exec = MpiExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify hostfile or host option is included
        self.assertTrue(
            'host' in cmd.lower(),
            "Hostfile option should be in MPI command"
        )

    def test_remainder_calculation(self):
        """Test that remainder nprocs are calculated correctly"""
        exec_info = MpiExecInfo(
            nprocs=10,
            hostfile=self.hostfile
        )

        cmd_list = [
            {'cmd': 'cmd1', 'nprocs': 2},
            {'cmd': 'cmd2', 'nprocs': 3},
            {'cmd': 'cmd3', 'nprocs': None}  # Should get 10 - 2 - 3 = 5
        ]

        mpi_exec = MpiExec(cmd_list, exec_info)

        # Access internal cmd_list to verify calculation
        processed_list = mpi_exec._delegate.cmd_list
        self.assertEqual(processed_list[2]['nprocs'], 5)

    def test_nprocs_overflow(self):
        """Test error when total nprocs exceeds available"""
        exec_info = MpiExecInfo(
            nprocs=5,
            hostfile=self.hostfile
        )

        cmd_list = [
            {'cmd': 'cmd1', 'nprocs': 3},
            {'cmd': 'cmd2', 'nprocs': 3},  # Total = 6, exceeds 5
            {'cmd': 'cmd3', 'nprocs': None}
        ]

        with self.assertRaises(ValueError):
            MpiExec(cmd_list, exec_info)


class TestOpenMpiExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_openmpi_specific_flags(self):
        """Test OpenMPI-specific flags"""
        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile
        )

        mpi_exec = OpenMpiExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify OpenMPI-specific flags
        self.assertIn('--oversubscribe', cmd)
        self.assertIn('--allow-run-as-root', cmd)

    def test_openmpi_env_format(self):
        """Test OpenMPI environment variable format"""
        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={'TEST_VAR': 'value'}
        )

        mpi_exec = OpenMpiExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # OpenMPI uses -x for environment variables
        self.assertIn('-x', cmd)


class TestMpichExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_mpich_env_format(self):
        """Test MPICH environment variable format"""
        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={'TEST_VAR': 'value'}
        )

        mpi_exec = MpichExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # MPICH uses -genv for environment variables
        self.assertIn('-genv', cmd)


class TestCrayMpichExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_cray_env_format(self):
        """Test Cray MPICH environment variable format"""
        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={'TEST_VAR': 'value'}
        )

        mpi_exec = CrayMpichExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Cray MPICH uses --env for environment variables
        self.assertIn('--env', cmd)


if __name__ == '__main__':
    unittest.main()
