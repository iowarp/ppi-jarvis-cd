"""
Tests for process utility classes in jarvis_cd.shell.process
"""
import unittest
import sys
import os
import tempfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.shell.process import (
    Kill, KillAll, Which, Mkdir, Rm, Chmod, Sleep, Echo, GdbServer
)
from jarvis_cd.shell.exec_info import LocalExecInfo


class TestKill(unittest.TestCase):
    """Tests for Kill class"""

    def test_kill_with_partial(self):
        """Test kill command construction with partial matching"""
        # Just test command construction, don't run it
        kill = Kill('nonexistent_test_process_xyz', partial=True)
        cmd = kill.cmd
        self.assertIn('pkill', cmd)
        self.assertIn('-9', cmd)
        self.assertIn('-f', cmd)
        self.assertIn('nonexistent_test_process_xyz', cmd)

    def test_kill_without_partial(self):
        """Test kill command construction without partial matching"""
        # Just test command construction, don't run it
        kill = Kill('nonexistent_test_process_abc', partial=False)
        cmd = kill.cmd
        self.assertIn('pkill', cmd)
        self.assertIn('-9', cmd)
        self.assertNotIn('-f', cmd)
        self.assertIn('nonexistent_test_process_abc', cmd)

    def test_kill_with_exec_info(self):
        """Test kill with custom exec info"""
        exec_info = LocalExecInfo()
        kill = Kill('nonexistent_myprocess_123', exec_info=exec_info)
        # Just verify the object is created properly
        self.assertIsNotNone(kill.cmd)
        self.assertIn('pkill', kill.cmd)


class TestKillAll(unittest.TestCase):
    """Tests for KillAll class"""

    def test_killall_command(self):
        """Test killall command construction"""
        # Just test command construction, don't run it (dangerous!)
        killall = KillAll()
        cmd = killall.cmd
        self.assertIn('pkill', cmd)
        self.assertIn('-9', cmd)
        self.assertIn('-u', cmd)
        self.assertIn('$(whoami)', cmd)

    def test_killall_with_exec_info(self):
        """Test killall with custom exec info"""
        exec_info = LocalExecInfo()
        killall = KillAll(exec_info=exec_info)
        # Just verify object creation
        self.assertIsNotNone(killall.cmd)
        self.assertIn('pkill', killall.cmd)


class TestWhich(unittest.TestCase):
    """Tests for Which class"""

    def test_which_python(self):
        """Test finding python executable"""
        which = Which('python3')
        which.run()

        self.assertEqual(which.exit_code['localhost'], 0)
        self.assertTrue(which.exists())
        self.assertIn('python', which.get_path().lower())

    def test_which_nonexistent(self):
        """Test finding non-existent executable"""
        which = Which('nonexistent_executable_12345')
        which.run()

        self.assertFalse(which.exists())
        self.assertEqual(which.get_path(), '')

    def test_which_command_construction(self):
        """Test which command construction"""
        which = Which('bash')
        which.run()
        cmd = which.get_cmd()
        self.assertEqual(cmd, 'which bash')


class TestMkdir(unittest.TestCase):
    """Tests for Mkdir class"""

    def setUp(self):
        """Set up test directory"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_mkdir_')

    def tearDown(self):
        """Clean up test directory"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mkdir_single_path(self):
        """Test creating single directory"""
        new_dir = os.path.join(self.test_dir, 'test_dir')
        mkdir = Mkdir(new_dir)
        mkdir.run()

        self.assertEqual(mkdir.exit_code['localhost'], 0)
        self.assertTrue(os.path.exists(new_dir))

    def test_mkdir_multiple_paths(self):
        """Test creating multiple directories"""
        paths = [
            os.path.join(self.test_dir, 'dir1'),
            os.path.join(self.test_dir, 'dir2'),
            os.path.join(self.test_dir, 'dir3')
        ]
        mkdir = Mkdir(paths)
        mkdir.run()

        self.assertEqual(mkdir.exit_code['localhost'], 0)
        for path in paths:
            self.assertTrue(os.path.exists(path))

    def test_mkdir_with_parents(self):
        """Test creating nested directories with parent flag"""
        nested_dir = os.path.join(self.test_dir, 'parent', 'child', 'grandchild')
        mkdir = Mkdir(nested_dir, parents=True)
        mkdir.run()

        self.assertEqual(mkdir.exit_code['localhost'], 0)
        self.assertTrue(os.path.exists(nested_dir))

    def test_mkdir_command_construction(self):
        """Test mkdir command construction"""
        mkdir = Mkdir('/tmp/test', parents=True)
        mkdir.run()
        cmd = mkdir.get_cmd()
        self.assertIn('mkdir', cmd)
        self.assertIn('-p', cmd)
        self.assertIn('/tmp/test', cmd)


class TestRm(unittest.TestCase):
    """Tests for Rm class"""

    def setUp(self):
        """Set up test files/directories"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_rm_')
        self.test_file = os.path.join(self.test_dir, 'test_file.txt')
        with open(self.test_file, 'w') as f:
            f.write('test content')

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_rm_single_file(self):
        """Test removing single file"""
        rm = Rm(self.test_file)
        rm.run()

        self.assertEqual(rm.exit_code['localhost'], 0)
        self.assertFalse(os.path.exists(self.test_file))

    def test_rm_multiple_files(self):
        """Test removing multiple files"""
        file1 = os.path.join(self.test_dir, 'file1.txt')
        file2 = os.path.join(self.test_dir, 'file2.txt')

        with open(file1, 'w') as f:
            f.write('test1')
        with open(file2, 'w') as f:
            f.write('test2')

        rm = Rm([file1, file2])
        rm.run()

        self.assertEqual(rm.exit_code['localhost'], 0)
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))

    def test_rm_directory_recursive(self):
        """Test removing directory recursively"""
        test_subdir = os.path.join(self.test_dir, 'subdir')
        os.makedirs(test_subdir)

        rm = Rm(test_subdir, recursive=True)
        rm.run()

        self.assertEqual(rm.exit_code['localhost'], 0)
        self.assertFalse(os.path.exists(test_subdir))

    def test_rm_command_construction(self):
        """Test rm command construction"""
        rm = Rm('/tmp/test', recursive=True, force=True)
        rm.run()
        cmd = rm.get_cmd()
        self.assertIn('rm', cmd)
        self.assertIn('-r', cmd)
        self.assertIn('-f', cmd)


class TestChmod(unittest.TestCase):
    """Tests for Chmod class"""

    def setUp(self):
        """Set up test file"""
        self.test_dir = tempfile.mkdtemp(prefix='jarvis_test_chmod_')
        self.test_file = os.path.join(self.test_dir, 'test_file.txt')
        with open(self.test_file, 'w') as f:
            f.write('test content')

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_chmod_single_file(self):
        """Test changing permissions on single file"""
        chmod = Chmod(self.test_file, '755')
        chmod.run()

        self.assertEqual(chmod.exit_code['localhost'], 0)

        # Check permissions changed
        import stat
        st = os.stat(self.test_file)
        mode = st.st_mode
        self.assertTrue(mode & stat.S_IRUSR)  # User read
        self.assertTrue(mode & stat.S_IWUSR)  # User write
        self.assertTrue(mode & stat.S_IXUSR)  # User execute

    def test_chmod_multiple_files(self):
        """Test changing permissions on multiple files"""
        file1 = os.path.join(self.test_dir, 'file1.txt')
        file2 = os.path.join(self.test_dir, 'file2.txt')

        with open(file1, 'w') as f:
            f.write('test1')
        with open(file2, 'w') as f:
            f.write('test2')

        chmod = Chmod([file1, file2], '+x')
        chmod.run()

        self.assertEqual(chmod.exit_code['localhost'], 0)

    def test_chmod_command_construction(self):
        """Test chmod command construction"""
        chmod = Chmod('/tmp/test', '644', recursive=True)
        chmod.run()
        cmd = chmod.get_cmd()
        self.assertIn('chmod', cmd)
        self.assertIn('-R', cmd)
        self.assertIn('644', cmd)


class TestSleep(unittest.TestCase):
    """Tests for Sleep class"""

    def test_sleep_integer(self):
        """Test sleep with integer duration"""
        sleep = Sleep(1)
        sleep.run()
        cmd = sleep.get_cmd()
        self.assertEqual(cmd, 'sleep 1')
        self.assertEqual(sleep.exit_code['localhost'], 0)

    def test_sleep_float(self):
        """Test sleep with float duration"""
        sleep = Sleep(0.1)
        sleep.run()
        cmd = sleep.get_cmd()
        self.assertEqual(cmd, 'sleep 0.1')
        self.assertEqual(sleep.exit_code['localhost'], 0)

    def test_sleep_with_exec_info(self):
        """Test sleep with custom exec info"""
        exec_info = LocalExecInfo()
        sleep = Sleep(1, exec_info=exec_info)
        sleep.run()
        self.assertEqual(sleep.exit_code['localhost'], 0)


class TestEcho(unittest.TestCase):
    """Tests for Echo class"""

    def test_echo_simple_text(self):
        """Test echoing simple text"""
        echo = Echo("Hello World")
        echo.run()

        self.assertEqual(echo.exit_code['localhost'], 0)
        self.assertIn("Hello World", echo.stdout['localhost'])

    def test_echo_with_special_chars(self):
        """Test echoing text with special characters"""
        text = "Test: $VAR ${PATH} `date`"
        echo = Echo(text)
        echo.run()

        self.assertEqual(echo.exit_code['localhost'], 0)
        # The output will have shell expansion, just check command succeeds

    def test_echo_command_construction(self):
        """Test echo command construction"""
        echo = Echo("test message")
        echo.run()
        cmd = echo.get_cmd()
        self.assertIn('echo', cmd)
        self.assertIn('test message', cmd)


class TestGdbServer(unittest.TestCase):
    """Tests for GdbServer class"""

    def test_gdbserver_command_construction(self):
        """Test gdbserver command construction"""
        gdbserver = GdbServer("./myapp", 1234)
        # Don't run it since gdbserver may not be installed
        cmd = gdbserver.cmd
        self.assertIn('gdbserver', cmd)
        self.assertIn(':1234', cmd)
        self.assertIn('./myapp', cmd)
        self.assertEqual(gdbserver.port, 1234)

    def test_gdbserver_with_exec_info(self):
        """Test gdbserver with custom exec info"""
        exec_info = LocalExecInfo()
        gdbserver = GdbServer("/bin/true", 5555, exec_info=exec_info)
        cmd = gdbserver.cmd
        self.assertIn('gdbserver', cmd)
        self.assertIn(':5555', cmd)
        self.assertEqual(gdbserver.port, 5555)


if __name__ == '__main__':
    unittest.main()
