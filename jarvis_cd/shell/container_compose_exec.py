"""
Container compose execution classes for Docker and Podman.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
from .core_exec import CoreExec, LocalExec
from .exec_info import ExecInfo


class PodmanBuildExec(CoreExec):
    """
    Execute podman compose build command.
    """

    def __init__(self, compose_file: str, exec_info: ExecInfo):
        """
        Initialize podman compose build.

        :param compose_file: Path to compose file
        :param exec_info: Execution information
        """
        super().__init__()
        self.compose_file = Path(compose_file)
        self.exec_info = exec_info
        self.local_exec = None

        if not self.compose_file.exists():
            raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

    def get_cmd(self) -> str:
        """Get the podman compose build command string"""
        import shutil
        # Use podman-compose if available, otherwise use podman compose
        if shutil.which('podman-compose'):
            return f"podman-compose -f {self.compose_file} build"
        else:
            # Check if podman has compose subcommand
            from .exec_info import LocalExecInfo
            test_exec = LocalExec('podman compose --help', LocalExecInfo())
            if test_exec.exit_code == 0:
                return f"podman compose -f {self.compose_file} build"

            raise RuntimeError(
                "podman-compose not found and podman compose subcommand not available. "
                "Please install podman-compose: pip install podman-compose"
            )

    def run(self):
        """Execute the podman compose build command"""
        cmd = self.get_cmd()
        self.local_exec = LocalExec(cmd, self.exec_info)

        # Copy state from LocalExec
        self.exit_code = self.local_exec.exit_code
        self.stdout = self.local_exec.stdout
        self.stderr = self.local_exec.stderr
        self.processes = self.local_exec.processes
        self.output_threads = self.local_exec.output_threads


class DockerBuildExec(CoreExec):
    """
    Execute docker compose build command.
    """

    def __init__(self, compose_file: str, exec_info: ExecInfo):
        """
        Initialize docker compose build.

        :param compose_file: Path to compose file
        :param exec_info: Execution information
        """
        super().__init__()
        self.compose_file = Path(compose_file)
        self.exec_info = exec_info
        self.local_exec = None

        if not self.compose_file.exists():
            raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

    def get_cmd(self) -> str:
        """Get the docker compose build command string"""
        return f"docker compose -f {self.compose_file} build"

    def run(self):
        """Execute the docker compose build command"""
        cmd = self.get_cmd()
        self.local_exec = LocalExec(cmd, self.exec_info)

        # Copy state from LocalExec
        self.exit_code = self.local_exec.exit_code
        self.stdout = self.local_exec.stdout
        self.stderr = self.local_exec.stderr
        self.processes = self.local_exec.processes
        self.output_threads = self.local_exec.output_threads


class ContainerBuildExec(CoreExec):
    """
    Router for container build - automatically selects between Docker and Podman.
    """

    def __init__(self, compose_file: str, exec_info: ExecInfo, prefer_podman: bool = False):
        """
        Initialize container build execution.

        :param compose_file: Path to compose file
        :param exec_info: Execution information
        :param prefer_podman: Prefer Podman over Docker if both available
        """
        super().__init__()
        self.compose_file = Path(compose_file)
        self.exec_info = exec_info
        self.prefer_podman = prefer_podman
        self.delegate = None

        # Determine which build implementation to use
        self._select_implementation()

    def _select_implementation(self):
        """Select Docker or Podman based on availability"""
        import shutil

        has_docker = shutil.which('docker') is not None
        has_podman = shutil.which('podman') is not None or shutil.which('podman-compose') is not None

        if self.prefer_podman and has_podman:
            self.delegate = PodmanBuildExec(self.compose_file, self.exec_info)
        elif has_docker:
            self.delegate = DockerBuildExec(self.compose_file, self.exec_info)
        elif has_podman:
            self.delegate = PodmanBuildExec(self.compose_file, self.exec_info)
        else:
            raise RuntimeError("Neither docker nor podman found in PATH")

    def get_cmd(self) -> str:
        """Get the command string from delegate"""
        return self.delegate.get_cmd()

    def run(self):
        """Execute the build command via delegate"""
        self.delegate.run()

        # Copy state from delegate
        self.exit_code = self.delegate.exit_code
        self.stdout = self.delegate.stdout
        self.stderr = self.delegate.stderr
        self.processes = self.delegate.processes
        self.output_threads = self.delegate.output_threads


class PodmanComposeExec(CoreExec):
    """
    Execute podman compose commands.
    """

    def __init__(self, compose_file: str, exec_info: ExecInfo, action: str = 'up'):
        """
        Initialize podman compose execution.

        :param compose_file: Path to compose file
        :param exec_info: Execution information
        :param action: Compose action (up, down, etc.)
        """
        super().__init__()
        self.compose_file = Path(compose_file)
        self.exec_info = exec_info
        self.action = action
        self.local_exec = None

        if not self.compose_file.exists():
            raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

    def get_cmd(self) -> str:
        """Get the podman compose command string"""
        import shutil
        # Use podman-compose if available, otherwise use podman compose
        if shutil.which('podman-compose'):
            cmd = f"podman-compose -f {self.compose_file} {self.action}"
        else:
            # Check if podman has compose subcommand
            from .exec_info import LocalExecInfo
            test_exec = LocalExec('podman compose --help', LocalExecInfo())
            if test_exec.exit_code == 0:
                cmd = f"podman compose -f {self.compose_file} {self.action}"
            else:
                raise RuntimeError(
                    "podman-compose not found and podman compose subcommand not available. "
                    "Please install podman-compose: pip install podman-compose"
                )
        # For 'up', add flags to show output and exit when container stops
        if self.action == 'up':
            cmd += " --abort-on-container-exit"
        return cmd

    def run(self):
        """Execute the podman compose command"""
        cmd = self.get_cmd()
        self.local_exec = LocalExec(cmd, self.exec_info)

        # Copy state from LocalExec
        self.exit_code = self.local_exec.exit_code
        self.stdout = self.local_exec.stdout
        self.stderr = self.local_exec.stderr
        self.processes = self.local_exec.processes
        self.output_threads = self.local_exec.output_threads


class DockerComposeExec(CoreExec):
    """
    Execute docker compose commands.
    """

    def __init__(self, compose_file: str, exec_info: ExecInfo, action: str = 'up'):
        """
        Initialize docker compose execution.

        :param compose_file: Path to compose file
        :param exec_info: Execution information
        :param action: Compose action (up, down, etc.)
        """
        super().__init__()
        self.compose_file = Path(compose_file)
        self.exec_info = exec_info
        self.action = action
        self.local_exec = None

        if not self.compose_file.exists():
            raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

    def get_cmd(self) -> str:
        """Get the docker compose command string"""
        cmd = f"docker compose -f {self.compose_file} {self.action}"
        # For 'up', add flags to show output and exit when container stops
        if self.action == 'up':
            cmd += " --abort-on-container-exit"
        return cmd

    def run(self):
        """Execute the docker compose command"""
        cmd = self.get_cmd()
        self.local_exec = LocalExec(cmd, self.exec_info)

        # Copy state from LocalExec
        self.exit_code = self.local_exec.exit_code
        self.stdout = self.local_exec.stdout
        self.stderr = self.local_exec.stderr
        self.processes = self.local_exec.processes
        self.output_threads = self.local_exec.output_threads


class ContainerComposeExec(CoreExec):
    """
    Router for container compose execution - automatically selects
    between Docker and Podman based on availability or configuration.
    """

    def __init__(self, compose_file: str, exec_info: ExecInfo, action: str = 'up',
                 prefer_podman: bool = False):
        """
        Initialize container compose execution.

        :param compose_file: Path to compose file
        :param exec_info: Execution information
        :param action: Compose action (up, down, etc.)
        :param prefer_podman: Prefer Podman over Docker if both available
        """
        super().__init__()
        self.compose_file = Path(compose_file)
        self.exec_info = exec_info
        self.action = action
        self.prefer_podman = prefer_podman
        self.delegate = None

        # Determine which compose implementation to use
        self._select_implementation()

    def _select_implementation(self):
        """Select Docker or Podman based on availability"""
        import shutil

        has_docker = shutil.which('docker') is not None
        has_podman = shutil.which('podman') is not None or shutil.which('podman-compose') is not None

        if self.prefer_podman and has_podman:
            self.delegate = PodmanComposeExec(self.compose_file, self.exec_info, self.action)
        elif has_docker:
            self.delegate = DockerComposeExec(self.compose_file, self.exec_info, self.action)
        elif has_podman:
            self.delegate = PodmanComposeExec(self.compose_file, self.exec_info, self.action)
        else:
            raise RuntimeError("Neither docker nor podman found in PATH")

    def get_cmd(self) -> str:
        """Get the command string from delegate"""
        return self.delegate.get_cmd()

    def run(self):
        """Execute the compose command via delegate"""
        self.delegate.run()

        # Copy state from delegate
        self.exit_code = self.delegate.exit_code
        self.stdout = self.delegate.stdout
        self.stderr = self.delegate.stderr
        self.processes = self.delegate.processes
        self.output_threads = self.delegate.output_threads
