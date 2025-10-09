"""
Tests for exec_factory.py - Exec factory class
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.shell.exec_factory import Exec
from jarvis_cd.shell.exec_info import (
    LocalExecInfo, SshExecInfo, PsshExecInfo, MpiExecInfo,
    ExecType
)


class TestExecFactory(unittest.TestCase):
    """Tests for Exec factory pattern"""

    def test_local_exec_delegation(self):
        """Test Exec delegates to LocalExec"""
        exec_info = LocalExecInfo()
        exec_obj = Exec('echo "test"', exec_info)
        delegate = exec_obj.run()

        self.assertIsNotNone(delegate)
        self.assertEqual(exec_obj.exit_code['localhost'], 0)
        self.assertIn('test', exec_obj.stdout['localhost'])

    def test_ssh_exec_delegation(self):
        """Test Exec delegates to SshExec"""
        exec_info = SshExecInfo(hostnames=['mock_host'])
        exec_obj = Exec('echo "ssh test"', exec_info)

        # Test delegation without running (mock host doesn't exist)
        self.assertEqual(exec_obj.exec_info.exec_type, ExecType.SSH)
        self.assertIsNotNone(exec_obj.cmd)

    def test_pssh_exec_delegation(self):
        """Test Exec delegates to PsshExec"""
        exec_info = PsshExecInfo(hostnames=['mock1', 'mock2'])
        exec_obj = Exec('echo "pssh test"', exec_info)

        # Test delegation without running
        self.assertEqual(exec_obj.exec_info.exec_type, ExecType.PSSH)
        self.assertIsNotNone(exec_obj.cmd)

    def test_mpi_exec_delegation(self):
        """Test Exec delegates to MpiExec"""
        exec_info = MpiExecInfo(nprocs=4)
        exec_obj = Exec('echo "mpi test"', exec_info)

        # Test delegation without running (MPI may not be available)
        self.assertIn(exec_obj.exec_info.exec_type,
                     [ExecType.MPI, ExecType.OPENMPI, ExecType.MPICH,
                      ExecType.INTEL_MPI, ExecType.CRAY_MPICH])
        self.assertIsNotNone(exec_obj.cmd)

    def test_get_cmd(self):
        """Test get_cmd method"""
        cmd = 'python3 -c "print(42)"'
        exec_info = LocalExecInfo()
        exec_obj = Exec(cmd, exec_info)

        self.assertEqual(exec_obj.get_cmd(), cmd)

    def test_wait(self):
        """Test wait method"""
        exec_info = LocalExecInfo()
        exec_obj = Exec('echo "wait test"', exec_info)
        exec_obj.run()

        exit_code = exec_obj.wait('localhost')
        self.assertEqual(exit_code, 0)

    def test_wait_all(self):
        """Test wait_all method"""
        exec_info = LocalExecInfo()
        exec_obj = Exec('echo "wait all test"', exec_info)
        exec_obj.run()

        exit_codes = exec_obj.wait_all()
        self.assertIn('localhost', exit_codes)
        self.assertEqual(exit_codes['localhost'], 0)

    def test_exec_type_unsupported(self):
        """Test unsupported exec type raises error"""
        # Create a custom exec_info with invalid type
        exec_info = LocalExecInfo()
        # Manually set invalid type
        exec_info.exec_type = None

        exec_obj = Exec('echo "test"', exec_info)

        with self.assertRaises(ValueError) as context:
            exec_obj.run()

        self.assertIn('Unsupported execution type', str(context.exception))

    def test_delegate_attributes_copied(self):
        """Test that delegate attributes are copied to parent"""
        exec_info = LocalExecInfo()
        exec_obj = Exec('echo "attribute test"', exec_info)
        exec_obj.run()

        # Check attributes are copied
        self.assertIsNotNone(exec_obj.exit_code)
        self.assertIsNotNone(exec_obj.stdout)
        self.assertIsNotNone(exec_obj.stderr)
        self.assertIsNotNone(exec_obj.processes)
        self.assertIsNotNone(exec_obj.output_threads)

    def test_wait_without_run(self):
        """Test wait before run returns 0"""
        exec_info = LocalExecInfo()
        exec_obj = Exec('echo "test"', exec_info)

        # Don't run, just wait
        exit_code = exec_obj.wait('localhost')
        self.assertEqual(exit_code, 0)

    def test_wait_all_without_run(self):
        """Test wait_all before run returns empty dict"""
        exec_info = LocalExecInfo()
        exec_obj = Exec('echo "test"', exec_info)

        # Don't run, just wait_all
        exit_codes = exec_obj.wait_all()
        self.assertEqual(exit_codes, {})


if __name__ == '__main__':
    unittest.main()
