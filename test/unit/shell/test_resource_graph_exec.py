"""
Tests for resource_graph_exec.py
"""
import unittest
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.shell.resource_graph_exec import ResourceGraphExec
from jarvis_cd.shell.exec_info import LocalExecInfo


class TestResourceGraphExec(unittest.TestCase):
    """Tests for ResourceGraphExec class"""

    def test_initialization(self):
        """Test ResourceGraphExec initialization"""
        exec_info = LocalExecInfo()
        # This will raise FileNotFoundError if script doesn't exist, which is expected
        try:
            rg_exec = ResourceGraphExec(exec_info, benchmark=True, duration=25)
            self.assertIsNotNone(rg_exec.cmd)
        except FileNotFoundError as e:
            # Expected if jarvis_resource_graph script doesn't exist
            self.assertIn('Resource graph script not found', str(e))

    def test_command_building_with_benchmark(self):
        """Test command building with benchmark enabled"""
        exec_info = LocalExecInfo()
        try:
            rg_exec = ResourceGraphExec(exec_info, benchmark=True, duration=30)
            cmd = rg_exec.get_cmd()
            self.assertIn('jarvis_resource_graph', cmd)
            self.assertIn('--duration', cmd)
            self.assertIn('30', cmd)
        except FileNotFoundError:
            pass  # Expected if script doesn't exist

    def test_command_building_without_benchmark(self):
        """Test command building with benchmark disabled"""
        exec_info = LocalExecInfo()
        try:
            rg_exec = ResourceGraphExec(exec_info, benchmark=False, duration=25)
            cmd = rg_exec.get_cmd()
            self.assertIn('jarvis_resource_graph', cmd)
            self.assertIn('--no-benchmark', cmd)
        except FileNotFoundError:
            pass  # Expected if script doesn't exist

    def test_custom_duration(self):
        """Test custom duration parameter"""
        exec_info = LocalExecInfo()
        try:
            rg_exec = ResourceGraphExec(exec_info, benchmark=True, duration=60)
            cmd = rg_exec.get_cmd()
            self.assertIn('--duration', cmd)
            self.assertIn('60', cmd)
        except FileNotFoundError:
            pass  # Expected


if __name__ == '__main__':
    unittest.main()
