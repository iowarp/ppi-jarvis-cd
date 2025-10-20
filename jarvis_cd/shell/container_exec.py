"""
Container execution classes for running commands inside Docker and Podman containers.
"""
from typing import Optional
from .core_exec import CoreExec, LocalExec
from .exec_info import ExecInfo


class PodmanContainerExec(CoreExec):
    """
    Execute commands inside a running Podman container.
    """

    def __init__(self, container_name: str, command: str, exec_info: ExecInfo):
        """
        Initialize podman container exec.

        :param container_name: Name of the running container
        :param command: Command to execute inside container
        :param exec_info: Execution information
        """
        super().__init__()
        self.container_name = container_name
        self.command = command
        self.exec_info = exec_info
        self.local_exec = None

    def get_cmd(self) -> str:
        """Get the podman exec command string"""
        return f"podman exec {self.container_name} {self.command}"

    def run(self):
        """Execute the command inside the container"""
        cmd = self.get_cmd()
        self.local_exec = LocalExec(cmd, self.exec_info)

        # Copy state from LocalExec
        self.exit_code = self.local_exec.exit_code
        self.stdout = self.local_exec.stdout
        self.stderr = self.local_exec.stderr
        self.processes = self.local_exec.processes
        self.output_threads = self.local_exec.output_threads


class DockerContainerExec(CoreExec):
    """
    Execute commands inside a running Docker container.
    """

    def __init__(self, container_name: str, command: str, exec_info: ExecInfo):
        """
        Initialize docker container exec.

        :param container_name: Name of the running container
        :param command: Command to execute inside container
        :param exec_info: Execution information
        """
        super().__init__()
        self.container_name = container_name
        self.command = command
        self.exec_info = exec_info
        self.local_exec = None

    def get_cmd(self) -> str:
        """Get the docker exec command string"""
        return f"docker exec {self.container_name} {self.command}"

    def run(self):
        """Execute the command inside the container"""
        cmd = self.get_cmd()
        self.local_exec = LocalExec(cmd, self.exec_info)

        # Copy state from LocalExec
        self.exit_code = self.local_exec.exit_code
        self.stdout = self.local_exec.stdout
        self.stderr = self.local_exec.stderr
        self.processes = self.local_exec.processes
        self.output_threads = self.local_exec.output_threads


class ContainerExec(CoreExec):
    """
    Router for container exec - automatically selects between Docker and Podman
    based on availability or configuration.
    """

    def __init__(self, container_name: str, command: str, exec_info: ExecInfo,
                 prefer_podman: bool = False):
        """
        Initialize container exec.

        :param container_name: Name of the running container
        :param command: Command to execute inside container
        :param exec_info: Execution information
        :param prefer_podman: Prefer Podman over Docker if both available
        """
        super().__init__()
        self.container_name = container_name
        self.command = command
        self.exec_info = exec_info
        self.prefer_podman = prefer_podman
        self.delegate = None

        # Determine which container runtime to use
        self._select_implementation()

    def _select_implementation(self):
        """Select Docker or Podman based on availability"""
        import shutil

        has_docker = shutil.which('docker') is not None
        has_podman = shutil.which('podman') is not None

        if self.prefer_podman and has_podman:
            self.delegate = PodmanContainerExec(self.container_name, self.command, self.exec_info)
        elif has_docker:
            self.delegate = DockerContainerExec(self.container_name, self.command, self.exec_info)
        elif has_podman:
            self.delegate = PodmanContainerExec(self.container_name, self.command, self.exec_info)
        else:
            raise RuntimeError("Neither docker nor podman found in PATH")

    def get_cmd(self) -> str:
        """Get the command string from delegate"""
        return self.delegate.get_cmd()

    def run(self):
        """Execute the command via delegate"""
        self.delegate.run()

        # Copy state from delegate
        self.exit_code = self.delegate.exit_code
        self.stdout = self.delegate.stdout
        self.stderr = self.delegate.stderr
        self.processes = self.delegate.processes
        self.output_threads = self.delegate.output_threads
