import unittest
import sys
import os
import tempfile
import time

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.shell.core_exec import LocalExec
from jarvis_cd.shell.exec_info import LocalExecInfo


class TestLocalExec(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_binary = os.path.join(os.path.dirname(__file__), 'test_env_checker')

        # Verify the test binary exists
        if not os.path.exists(self.test_binary):
            raise RuntimeError(f"Test binary not found: {self.test_binary}")

    def test_basic_execution(self):
        """Test basic command execution"""
        exec_info = LocalExecInfo()
        local_exec = LocalExec('echo "hello world"', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('hello world', local_exec.stdout['localhost'])

    def test_single_env_variable(self):
        """Test execution with a single environment variable"""
        exec_info = LocalExecInfo(env={'TEST_VAR': 'test_value'})
        local_exec = LocalExec(f'{self.test_binary} TEST_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('TEST_VAR=test_value', local_exec.stdout['localhost'])

    def test_multiple_env_variables(self):
        """Test execution with multiple environment variables"""
        exec_info = LocalExecInfo(env={
            'VAR1': 'value1',
            'VAR2': 'value2',
            'VAR3': 'value3'
        })
        local_exec = LocalExec(f'{self.test_binary} VAR1 VAR2 VAR3', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        stdout = local_exec.stdout['localhost']
        self.assertIn('VAR1=value1', stdout)
        self.assertIn('VAR2=value2', stdout)
        self.assertIn('VAR3=value3', stdout)

    def test_env_variable_with_special_chars(self):
        """Test environment variables with special characters"""
        special_value = "value with spaces and 'quotes' and \"double quotes\""
        exec_info = LocalExecInfo(env={'SPECIAL_VAR': special_value})
        local_exec = LocalExec(f'{self.test_binary} SPECIAL_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('SPECIAL_VAR=', local_exec.stdout['localhost'])

    def test_env_variable_override(self):
        """Test that custom env variables override system variables"""
        exec_info = LocalExecInfo(env={'PATH': '/custom/path'})
        local_exec = LocalExec(f'{self.test_binary} PATH', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('PATH=/custom/path', local_exec.stdout['localhost'])

    def test_empty_env(self):
        """Test execution with empty env dict"""
        exec_info = LocalExecInfo(env={})
        local_exec = LocalExec('echo "test"', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)

    def test_none_env(self):
        """Test execution with None env (should use system env)"""
        exec_info = LocalExecInfo(env=None)
        local_exec = LocalExec(f'{self.test_binary} PATH', exec_info)

        # PATH should exist in system environment
        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('PATH=', local_exec.stdout['localhost'])

    def test_collect_output(self):
        """Test output collection"""
        exec_info = LocalExecInfo(collect_output=True)
        local_exec = LocalExec('echo "collected output"', exec_info)

        self.assertIn('collected output', local_exec.stdout['localhost'])

    def test_hide_output(self):
        """Test hiding output (should still collect)"""
        exec_info = LocalExecInfo(hide_output=True, collect_output=True)
        local_exec = LocalExec('echo "hidden output"', exec_info)

        self.assertIn('hidden output', local_exec.stdout['localhost'])

    def test_stderr_collection(self):
        """Test stderr collection"""
        exec_info = LocalExecInfo(collect_output=True)
        local_exec = LocalExec('echo "error message" >&2', exec_info)

        self.assertIn('error message', local_exec.stderr['localhost'])

    def test_pipe_stdout_to_file(self):
        """Test piping stdout to a file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name

        try:
            exec_info = LocalExecInfo(pipe_stdout=temp_file)
            local_exec = LocalExec('echo "piped output"', exec_info)

            with open(temp_file, 'r') as f:
                content = f.read()
            self.assertIn('piped output', content)
        finally:
            os.unlink(temp_file)

    def test_pipe_stderr_to_file(self):
        """Test piping stderr to a file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name

        try:
            exec_info = LocalExecInfo(pipe_stderr=temp_file)
            local_exec = LocalExec('echo "error output" >&2', exec_info)

            with open(temp_file, 'r') as f:
                content = f.read()
            self.assertIn('error output', content)
        finally:
            os.unlink(temp_file)

    def test_cwd_change(self):
        """Test changing working directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            exec_info = LocalExecInfo(cwd=tmpdir)
            local_exec = LocalExec('pwd', exec_info)

            self.assertIn(tmpdir, local_exec.stdout['localhost'])

    def test_async_execution(self):
        """Test asynchronous execution"""
        exec_info = LocalExecInfo(exec_async=True)
        local_exec = LocalExec('sleep 0.1 && echo "async done"', exec_info)

        # Process should still be running or just finished
        # Wait for it to complete
        exit_code = local_exec.wait('localhost')
        self.assertEqual(exit_code, 0)
        self.assertIn('async done', local_exec.stdout['localhost'])

    def test_sleep_ms(self):
        """Test sleep after execution"""
        exec_info = LocalExecInfo(sleep_ms=100)
        start_time = time.time()
        local_exec = LocalExec('echo "test"', exec_info)
        elapsed = time.time() - start_time

        # Should have slept for at least 0.1 seconds
        self.assertGreaterEqual(elapsed, 0.1)

    def test_stdin_input(self):
        """Test providing stdin to command"""
        exec_info = LocalExecInfo(stdin="test input\n")
        local_exec = LocalExec('cat', exec_info)

        self.assertIn('test input', local_exec.stdout['localhost'])

    def test_exit_code_on_failure(self):
        """Test that exit code is captured on command failure"""
        exec_info = LocalExecInfo()
        local_exec = LocalExec('false', exec_info)

        self.assertNotEqual(local_exec.exit_code['localhost'], 0)

    def test_env_preserved_across_commands(self):
        """Test that environment variables persist across shell commands"""
        exec_info = LocalExecInfo(env={'CUSTOM_VAR': 'custom_value'})
        # Use shell to execute multiple commands
        cmd = f'{self.test_binary} CUSTOM_VAR && echo "second command"'
        local_exec = LocalExec(cmd, exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        stdout = local_exec.stdout['localhost']
        self.assertIn('CUSTOM_VAR=custom_value', stdout)
        self.assertIn('second command', stdout)

    def test_numeric_env_values(self):
        """Test environment variables with numeric values"""
        exec_info = LocalExecInfo(env={
            'INT_VAR': 42,
            'FLOAT_VAR': 3.14,
            'BOOL_VAR': True
        })
        local_exec = LocalExec(f'{self.test_binary} INT_VAR FLOAT_VAR BOOL_VAR', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        stdout = local_exec.stdout['localhost']
        self.assertIn('INT_VAR=42', stdout)
        self.assertIn('FLOAT_VAR=3.14', stdout)
        self.assertIn('BOOL_VAR=True', stdout)

    def test_env_with_equals_in_value(self):
        """Test environment variable with equals sign in value"""
        exec_info = LocalExecInfo(env={'CONFIG': 'key=value'})
        local_exec = LocalExec(f'{self.test_binary} CONFIG', exec_info)

        self.assertEqual(local_exec.exit_code['localhost'], 0)
        self.assertIn('CONFIG=key=value', local_exec.stdout['localhost'])

    def test_get_cmd(self):
        """Test get_cmd returns the original command"""
        cmd = 'echo "test command"'
        exec_info = LocalExecInfo()
        local_exec = LocalExec(cmd, exec_info)

        self.assertEqual(local_exec.get_cmd(), cmd)


if __name__ == '__main__':
    unittest.main()
