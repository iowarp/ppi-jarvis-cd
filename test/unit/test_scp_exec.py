import unittest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.shell.scp_exec import ScpExec, PscpExec, _Scp
from jarvis_cd.shell.exec_info import ScpExecInfo, PscpExecInfo
from jarvis_cd.util.hostfile import Hostfile


class TestScpExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"test content")
        self.test_file.close()
        self.hostfile = Hostfile(hosts=['testhost'], find_ips=False)

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)

    def test_scp_single_path(self):
        """Test SCP with single path"""
        exec_info = ScpExecInfo(hostfile=self.hostfile, exec_async=True)
        scp_exec = ScpExec(self.test_file.name, exec_info)

        self.assertEqual(len(scp_exec.scp_nodes), 1)
        cmd = scp_exec.get_cmd()
        self.assertIn('scp', cmd)
        self.assertIn(self.test_file.name, cmd)

    def test_scp_multiple_paths(self):
        """Test SCP with multiple paths"""
        exec_info = ScpExecInfo(hostfile=self.hostfile, exec_async=True)
        paths = [self.test_file.name, '/tmp/file2.txt']
        scp_exec = ScpExec(paths, exec_info)

        self.assertEqual(len(scp_exec.scp_nodes), 2)

    def test_scp_tuple_paths(self):
        """Test SCP with tuple paths (different src and dst)"""
        exec_info = ScpExecInfo(hostfile=self.hostfile, exec_async=True)
        paths = [(self.test_file.name, '/tmp/remote_file.txt')]
        scp_exec = ScpExec(paths, exec_info)

        self.assertEqual(len(scp_exec.scp_nodes), 1)
        cmd = scp_exec.get_cmd()
        self.assertIn('scp', cmd)

    def test_scp_requires_hostfile(self):
        """Test that SCP requires a hostfile"""
        exec_info = ScpExecInfo(hostfile=None, exec_async=True)

        with self.assertRaises(ValueError):
            ScpExec(self.test_file.name, exec_info)

    def test_scp_empty_paths_list(self):
        """Test that SCP requires at least one path"""
        exec_info = ScpExecInfo(hostfile=self.hostfile, exec_async=True)

        with self.assertRaises(ValueError):
            ScpExec([], exec_info)


class TestInternalScp(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"test content")
        self.test_file.close()
        self.hostfile = Hostfile(hosts=['testhost'], find_ips=False)

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)

    def test_rsync_basic_command(self):
        """Test basic rsync command construction"""
        exec_info = ScpExecInfo(hostfile=self.hostfile, exec_async=True)
        scp = _Scp(self.test_file.name, '/tmp/remote.txt', exec_info)

        cmd = scp.get_cmd()
        self.assertIn('rsync', cmd)
        self.assertIn(self.test_file.name, cmd)
        self.assertIn('testhost', cmd)

    def test_rsync_with_user(self):
        """Test rsync command with user"""
        exec_info = ScpExecInfo(
            user='testuser',
            hostfile=self.hostfile,
            exec_async=True
        )
        scp = _Scp(self.test_file.name, '/tmp/remote.txt', exec_info)

        cmd = scp.get_cmd()
        self.assertIn('testuser@testhost', cmd)

    def test_rsync_with_port(self):
        """Test rsync command with custom port"""
        exec_info = ScpExecInfo(
            port=2222,
            hostfile=self.hostfile,
            exec_async=True
        )
        scp = _Scp(self.test_file.name, '/tmp/remote.txt', exec_info)

        cmd = scp.get_cmd()
        self.assertIn('-p 2222', cmd)

    def test_rsync_with_pkey(self):
        """Test rsync command with private key"""
        exec_info = ScpExecInfo(
            pkey='/path/to/key.pem',
            hostfile=self.hostfile,
            exec_async=True
        )
        scp = _Scp(self.test_file.name, '/tmp/remote.txt', exec_info)

        cmd = scp.get_cmd()
        self.assertIn('-i /path/to/key.pem', cmd)

    def test_rsync_localhost_no_copy_same_path(self):
        """Test that rsync to localhost with same path does nothing"""
        localhost_hostfile = Hostfile(hosts=['localhost'], find_ips=False)
        exec_info = ScpExecInfo(hostfile=localhost_hostfile, exec_async=True)
        scp = _Scp(self.test_file.name, self.test_file.name, exec_info)

        # Should execute 'true' (no-op)
        cmd = scp.get_cmd()
        self.assertEqual(cmd, 'true')

    def test_rsync_localhost_copy_different_path(self):
        """Test that rsync to localhost with different path uses cp"""
        localhost_hostfile = Hostfile(hosts=['localhost'], find_ips=False)
        exec_info = ScpExecInfo(hostfile=localhost_hostfile, exec_async=True)
        scp = _Scp(self.test_file.name, '/tmp/copy.txt', exec_info)

        cmd = scp.get_cmd()
        self.assertIn('cp -r', cmd)
        self.assertNotIn('rsync', cmd)

    def test_rsync_combined_options(self):
        """Test rsync with multiple options"""
        exec_info = ScpExecInfo(
            user='testuser',
            port=2222,
            pkey='/path/to/key.pem',
            hostfile=self.hostfile,
            exec_async=True
        )
        scp = _Scp(self.test_file.name, '/tmp/remote.txt', exec_info)

        cmd = scp.get_cmd()
        self.assertIn('rsync', cmd)
        self.assertIn('testuser@testhost', cmd)
        self.assertIn('-p 2222', cmd)
        self.assertIn('-i /path/to/key.pem', cmd)


class TestPscpExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"test content")
        self.test_file.close()
        self.multi_host = Hostfile(hosts=['host1', 'host2', 'host3'], find_ips=False)

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)

    def test_pscp_requires_hostfile(self):
        """Test that PSCP requires a hostfile"""
        exec_info = PscpExecInfo(hostfile=None, exec_async=True)

        with self.assertRaises(ValueError):
            PscpExec(self.test_file.name, exec_info)

    def test_pscp_empty_hostfile(self):
        """Test that PSCP requires non-empty hostfile"""
        empty_hostfile = Hostfile(hosts=[], find_ips=False)
        exec_info = PscpExecInfo(hostfile=empty_hostfile, exec_async=True)

        with self.assertRaises(ValueError):
            PscpExec(self.test_file.name, exec_info)

    @patch('jarvis_cd.shell.scp_exec.ScpExec')
    def test_pscp_creates_scp_for_each_host(self, mock_scp_exec):
        """Test that PSCP creates SCP executor for each host"""
        exec_info = PscpExecInfo(hostfile=self.multi_host, exec_async=True)

        # Mock ScpExec to avoid actual execution
        mock_instances = []
        for i in range(3):
            mock_instance = MagicMock()
            mock_instance.wait_all_scp.return_value = {'localhost': 0}
            mock_instance.stdout = {'localhost': ''}
            mock_instance.stderr = {'localhost': ''}
            mock_instances.append(mock_instance)

        mock_scp_exec.side_effect = mock_instances

        pscp_exec = PscpExec(self.test_file.name, exec_info)

        # Should create 3 SCP executors, one for each host
        self.assertEqual(mock_scp_exec.call_count, 3)

    @patch('jarvis_cd.shell.scp_exec.ScpExec')
    def test_pscp_parallel_execution(self, mock_scp_exec):
        """Test that PSCP executes on all hosts in parallel"""
        exec_info = PscpExecInfo(hostfile=self.multi_host, exec_async=True)

        # Create mock instances for each host
        mock_instances = []
        for hostname in self.multi_host.hosts:
            mock_instance = MagicMock()
            mock_instance.wait_all_scp.return_value = {'localhost': 0}
            mock_instance.stdout = {'localhost': ''}
            mock_instance.stderr = {'localhost': ''}
            mock_instances.append(mock_instance)

        mock_scp_exec.side_effect = mock_instances

        pscp_exec = PscpExec(self.test_file.name, exec_info)

        # Verify SCP was created for each host
        self.assertEqual(mock_scp_exec.call_count, 3)

        # Check that each call had the correct single-host hostfile
        for i, call in enumerate(mock_scp_exec.call_args_list):
            scp_info = call[0][1]
            self.assertEqual(len(scp_info.hostfile.hosts), 1)
            self.assertIn(scp_info.hostfile.hosts[0], self.multi_host.hosts)

    def test_pscp_get_cmd(self):
        """Test that PSCP get_cmd returns description"""
        exec_info = PscpExecInfo(hostfile=self.multi_host, exec_async=True)

        with patch('jarvis_cd.shell.scp_exec.ScpExec'):
            pscp_exec = PscpExec(self.test_file.name, exec_info)
            cmd = pscp_exec.get_cmd()
            self.assertIn('pscp', cmd)
            self.assertIn('3 hosts', cmd)


if __name__ == '__main__':
    unittest.main()
