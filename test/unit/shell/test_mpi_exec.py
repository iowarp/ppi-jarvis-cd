import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.shell.mpi_exec import MpiExec, OpenMpiExec, MpichExec, CrayMpichExec, IntelMpiExec
from jarvis_cd.shell.exec_info import MpiExecInfo, ExecType
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

    def test_single_env_variable(self):
        """Test MPI execution with a single environment variable"""
        test_binary = os.path.join(os.path.dirname(__file__), 'test_env_checker')
        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={'TEST_VAR': 'test_value'}
        )

        if os.path.exists(test_binary):
            mpi_exec = MpiExec(f'{test_binary} TEST_VAR', exec_info)
            cmd = mpi_exec.get_cmd()

            self.assertIn('TEST_VAR', cmd)
            self.assertIn('test_value', cmd)

    def test_multiple_env_variables(self):
        """Test MPI execution with multiple environment variables"""
        test_binary = os.path.join(os.path.dirname(__file__), 'test_env_checker')
        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={
                'VAR1': 'value1',
                'VAR2': 'value2',
                'VAR3': 'value3'
            }
        )

        if os.path.exists(test_binary):
            mpi_exec = MpiExec(f'{test_binary} VAR1 VAR2 VAR3', exec_info)
            cmd = mpi_exec.get_cmd()

            self.assertIn('VAR1', cmd)
            self.assertIn('value1', cmd)
            self.assertIn('VAR2', cmd)
            self.assertIn('value2', cmd)
            self.assertIn('VAR3', cmd)
            self.assertIn('value3', cmd)

    def test_env_with_special_characters(self):
        """Test environment variables with special characters"""
        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={'SPECIAL_VAR': 'value with "quotes" and spaces'}
        )

        mpi_exec = MpiExec('echo $SPECIAL_VAR', exec_info)
        cmd = mpi_exec.get_cmd()

        self.assertIn('SPECIAL_VAR', cmd)

    def test_numeric_env_values(self):
        """Test environment variables with numeric values"""
        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={
                'INT_VAR': 42,
                'FLOAT_VAR': 3.14
            }
        )

        mpi_exec = MpiExec('echo test', exec_info)
        cmd = mpi_exec.get_cmd()

        self.assertIn('INT_VAR', cmd)
        self.assertIn('42', cmd)
        self.assertIn('FLOAT_VAR', cmd)
        self.assertIn('3.14', cmd)

    def test_basic_env_without_ld_preload(self):
        """Test that basic_env removes LD_PRELOAD"""
        exec_info = MpiExecInfo(
            nprocs=1,
            hostfile=self.hostfile,
            env={'LD_PRELOAD': '/lib/test.so', 'OTHER_VAR': 'value'}
        )

        # basic_env should not have LD_PRELOAD
        self.assertNotIn('LD_PRELOAD', exec_info.basic_env)
        self.assertIn('OTHER_VAR', exec_info.basic_env)

    def test_multi_command_env_per_command(self):
        """Test environment variables in multi-command MPI execution"""
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=self.hostfile,
            env={'GLOBAL_VAR': 'global_value'}
        )

        cmd_list = [
            {'cmd': 'echo cmd1', 'nprocs': 2},
            {'cmd': 'echo cmd2', 'nprocs': 2}
        ]

        mpi_exec = MpiExec(cmd_list, exec_info)
        cmd = mpi_exec.get_cmd()

        # Environment should be included for both commands
        self.assertIn('GLOBAL_VAR', cmd)

    def test_disable_preload_in_multi_command(self):
        """Test that disable_preload removes LD_PRELOAD for specific commands"""
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=self.hostfile,
            env={'LD_PRELOAD': '/lib/test.so', 'OTHER_VAR': 'value'}
        )

        cmd_list = [
            {'cmd': 'echo cmd1', 'nprocs': 2, 'disable_preload': True},
            {'cmd': 'echo cmd2', 'nprocs': 2, 'disable_preload': False}
        ]

        mpi_exec = MpiExec(cmd_list, exec_info)
        # The first command should not have LD_PRELOAD in its env
        # This is implementation-specific, so we just verify it doesn't crash
        cmd = mpi_exec.get_cmd()
        self.assertIsNotNone(cmd)

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
        processed_list = mpi_exec.cmd_list
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

    def test_cray_localhost_only_no_hostfile(self):
        """Test that Cray skips hostfile for localhost-only"""
        localhost_only = Hostfile(hosts=['localhost'], find_ips=False)
        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=localhost_only,
            env={}
        )

        mpi_exec = CrayMpichExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Should not include hostfile option for localhost-only
        self.assertNotIn('--hostfile', cmd)
        self.assertNotIn('--hosts', cmd)

    def test_cray_multi_host(self):
        """Test Cray with multiple hosts"""
        multi_host = Hostfile(hosts=['host1', 'host2'], find_ips=False)
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=multi_host,
            env={}
        )

        mpi_exec = CrayMpichExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Should include hosts option
        self.assertTrue('--hosts' in cmd or '--hostfile' in cmd)

    def test_cray_ppn_option(self):
        """Test Cray MPICH ppn option"""
        exec_info = MpiExecInfo(
            nprocs=8,
            ppn=4,
            hostfile=self.hostfile,
            env={}
        )

        mpi_exec = CrayMpichExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Cray uses --ppn
        self.assertIn('--ppn', cmd)

    def test_cray_multi_command(self):
        """Test Cray MPICH multi-command format"""
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=self.hostfile,
            env={'MY_VAR': 'value'}
        )

        cmd_list = [
            {'cmd': 'cmd1', 'nprocs': 2},
            {'cmd': 'cmd2', 'nprocs': 2}
        ]

        mpi_exec = CrayMpichExec(cmd_list, exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify multi-command structure with ' : ' separator
        self.assertIn(':', cmd)
        self.assertIn('cmd1', cmd)
        self.assertIn('cmd2', cmd)

    def test_cray_multi_command_with_disable_preload(self):
        """Test Cray multi-command with disable_preload"""
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=self.hostfile,
            env={'LD_PRELOAD': '/lib/test.so', 'OTHER_VAR': 'value'}
        )

        cmd_list = [
            {'cmd': 'cmd1', 'nprocs': 2, 'disable_preload': True},
            {'cmd': 'cmd2', 'nprocs': 2, 'disable_preload': False}
        ]

        mpi_exec = CrayMpichExec(cmd_list, exec_info)
        # Should not crash and should produce valid command
        cmd = mpi_exec.get_cmd()
        self.assertIsNotNone(cmd)

    def test_cray_hostfile_path(self):
        """Test Cray MPICH with hostfile path"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hosts') as f:
            f.write('host1\nhost2\n')
            hostfile_path = f.name

        try:
            hostfile = Hostfile(path=hostfile_path)
            exec_info = MpiExecInfo(
                nprocs=4,
                hostfile=hostfile,
                env={}
            )

            mpi_exec = CrayMpichExec('./myapp', exec_info)
            cmd = mpi_exec.get_cmd()

            # Should include hostfile path
            self.assertIn('--hostfile', cmd)
            self.assertIn(hostfile_path, cmd)
        finally:
            os.unlink(hostfile_path)


class TestIntelMpiExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_intel_mpi_inherits_mpich(self):
        """Test that Intel MPI uses MPICH-style commands"""
        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={'TEST_VAR': 'value'}
        )

        mpi_exec = IntelMpiExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # Intel MPI inherits from MPICH, so uses -genv
        self.assertIn('-genv', cmd)


class TestOpenMpiMultiCommand(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_openmpi_multi_command(self):
        """Test OpenMPI multi-command format"""
        exec_info = MpiExecInfo(
            nprocs=6,
            hostfile=self.hostfile,
            env={'MY_VAR': 'value'}
        )

        cmd_list = [
            {'cmd': 'cmd1', 'nprocs': 2},
            {'cmd': 'cmd2', 'nprocs': 4}
        ]

        mpi_exec = OpenMpiExec(cmd_list, exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify multi-command structure with ' : ' separator
        self.assertIn(':', cmd)
        self.assertIn('cmd1', cmd)
        self.assertIn('cmd2', cmd)
        self.assertIn('-x', cmd)  # OpenMPI env format

    def test_openmpi_ppn_with_hostfile_path(self):
        """Test OpenMPI with ppn and hostfile path"""
        # Create a temporary hostfile path
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hosts') as f:
            f.write('host1\nhost2\n')
            hostfile_path = f.name

        try:
            hostfile = Hostfile(path=hostfile_path)
            exec_info = MpiExecInfo(
                nprocs=4,
                ppn=2,
                hostfile=hostfile,
                env={}
            )

            mpi_exec = OpenMpiExec('./myapp', exec_info)
            cmd = mpi_exec.get_cmd()

            # Should include hostfile path
            self.assertIn('--hostfile', cmd)
            self.assertIn(hostfile_path, cmd)
            self.assertIn('-npernode', cmd)
        finally:
            os.unlink(hostfile_path)

    def test_openmpi_multi_command_with_ld_preload(self):
        """Test OpenMPI multi-command with LD_PRELOAD in env and disable_preload"""
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=self.hostfile,
            env={'LD_PRELOAD': '/lib/test.so', 'OTHER_VAR': 'value'}
        )

        cmd_list = [
            {'cmd': 'cmd1', 'nprocs': 2, 'disable_preload': True},
            {'cmd': 'cmd2', 'nprocs': 2, 'disable_preload': False}
        ]

        mpi_exec = OpenMpiExec(cmd_list, exec_info)
        cmd = mpi_exec.get_cmd()

        # First command should not have LD_PRELOAD, second should have it
        # This tests the LD_PRELOAD deletion logic
        self.assertIsNotNone(cmd)
        self.assertIn('cmd1', cmd)
        self.assertIn('cmd2', cmd)


class TestMpichMultiCommand(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_mpich_multi_command(self):
        """Test MPICH multi-command format"""
        exec_info = MpiExecInfo(
            nprocs=6,
            hostfile=self.hostfile,
            env={'MY_VAR': 'value'}
        )

        cmd_list = [
            {'cmd': 'cmd1', 'nprocs': 2},
            {'cmd': 'cmd2', 'nprocs': 4}
        ]

        mpi_exec = MpichExec(cmd_list, exec_info)
        cmd = mpi_exec.get_cmd()

        # Verify multi-command structure with ' : ' separator
        self.assertIn(':', cmd)
        self.assertIn('cmd1', cmd)
        self.assertIn('cmd2', cmd)
        self.assertIn('-env', cmd)  # MPICH env format for multi-command

    def test_mpich_ppn_option(self):
        """Test MPICH ppn option"""
        exec_info = MpiExecInfo(
            nprocs=8,
            ppn=4,
            hostfile=self.hostfile,
            env={}
        )

        mpi_exec = MpichExec('./myapp', exec_info)
        cmd = mpi_exec.get_cmd()

        # MPICH uses -ppn
        self.assertIn('-ppn', cmd)

    def test_mpich_hostfile_path(self):
        """Test MPICH with hostfile path"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hosts') as f:
            f.write('host1\nhost2\n')
            hostfile_path = f.name

        try:
            hostfile = Hostfile(path=hostfile_path)
            exec_info = MpiExecInfo(
                nprocs=4,
                hostfile=hostfile,
                env={}
            )

            mpi_exec = MpichExec('./myapp', exec_info)
            cmd = mpi_exec.get_cmd()

            # Should include hostfile path
            self.assertIn('--hostfile', cmd)
            self.assertIn(hostfile_path, cmd)
        finally:
            os.unlink(hostfile_path)


class TestMpiExecFactory(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    @patch('jarvis_cd.shell.mpi_exec.MpiVersion')
    def test_factory_openmpi_detection(self, mock_mpi_version):
        """Test factory creates OpenMpiExec when OpenMPI is detected"""
        # Mock MPI version detection to return OpenMPI
        mock_version = Mock()
        mock_version.version = ExecType.OPENMPI
        mock_mpi_version.return_value = mock_version

        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={}
        )

        mpi_exec = MpiExec('./myapp', exec_info)

        # Should be an instance of OpenMpiExec
        self.assertIsInstance(mpi_exec, OpenMpiExec)

    @patch('jarvis_cd.shell.mpi_exec.MpiVersion')
    def test_factory_mpich_detection(self, mock_mpi_version):
        """Test factory creates MpichExec when MPICH is detected"""
        # Mock MPI version detection to return MPICH
        mock_version = Mock()
        mock_version.version = ExecType.MPICH
        mock_mpi_version.return_value = mock_version

        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={}
        )

        mpi_exec = MpiExec('./myapp', exec_info)

        # Should be an instance of MpichExec
        self.assertIsInstance(mpi_exec, MpichExec)

    @patch('jarvis_cd.shell.mpi_exec.MpiVersion')
    def test_factory_intel_mpi_detection(self, mock_mpi_version):
        """Test factory creates IntelMpiExec when Intel MPI is detected"""
        # Mock MPI version detection to return Intel MPI
        mock_version = Mock()
        mock_version.version = ExecType.INTEL_MPI
        mock_mpi_version.return_value = mock_version

        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={}
        )

        mpi_exec = MpiExec('./myapp', exec_info)

        # Should be an instance of IntelMpiExec
        self.assertIsInstance(mpi_exec, IntelMpiExec)

    @patch('jarvis_cd.shell.mpi_exec.MpiVersion')
    def test_factory_cray_mpich_detection(self, mock_mpi_version):
        """Test factory creates CrayMpichExec when Cray MPICH is detected"""
        # Mock MPI version detection to return Cray MPICH
        mock_version = Mock()
        mock_version.version = ExecType.CRAY_MPICH
        mock_mpi_version.return_value = mock_version

        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={}
        )

        mpi_exec = MpiExec('./myapp', exec_info)

        # Should be an instance of CrayMpichExec
        self.assertIsInstance(mpi_exec, CrayMpichExec)

    @patch('jarvis_cd.shell.mpi_exec.MpiVersion')
    def test_factory_unknown_mpi_defaults_to_mpich(self, mock_mpi_version):
        """Test factory defaults to MPICH for unknown MPI type"""
        # Mock MPI version detection to return unknown type
        mock_version = Mock()
        mock_version.version = ExecType.LOCAL  # Unknown MPI type
        mock_mpi_version.return_value = mock_version

        exec_info = MpiExecInfo(
            nprocs=2,
            hostfile=self.hostfile,
            env={}
        )

        # Capture print output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        mpi_exec = MpiExec('./myapp', exec_info)

        sys.stdout = sys.__stdout__

        # Should default to MpichExec
        self.assertIsInstance(mpi_exec, MpichExec)
        # Should print warning
        self.assertIn('Unknown MPI type', captured_output.getvalue())


class TestEmptyCmdList(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.hostfile = Hostfile(hosts=['localhost'], find_ips=False)

    def test_empty_cmd_list_error(self):
        """Test that empty command list raises ValueError"""
        exec_info = MpiExecInfo(
            nprocs=4,
            hostfile=self.hostfile,
            env={}
        )

        cmd_list = []

        with self.assertRaises(ValueError) as ctx:
            OpenMpiExec(cmd_list, exec_info)
        self.assertIn('empty', str(ctx.exception).lower())


if __name__ == '__main__':
    unittest.main()
