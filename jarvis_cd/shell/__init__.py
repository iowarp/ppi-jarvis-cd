"""
Shell execution module for Jarvis-CD.

This module provides comprehensive command execution capabilities including:
- Local execution
- SSH/PSSH execution 
- MPI execution with auto-detection
- SCP/PSCP file transfer
- Utility commands

Usage examples:

# Local execution
from jarvis_cd.shell import LocalExecInfo, LocalExec
exec_info = LocalExecInfo()
result = LocalExec("ls -la", exec_info)

# SSH execution
from jarvis_cd.shell import SshExecInfo, SshExec, Hostfile
exec_info = SshExecInfo(hostfile=Hostfile(["remote.host.com"]))
result = SshExec("ls -la", exec_info)

# MPI execution
from jarvis_cd.shell import MpiExecInfo, MpiExec
exec_info = MpiExecInfo(nprocs=4)
result = MpiExec("./my_mpi_program", exec_info)

# File transfer
from jarvis_cd.shell import ScpExecInfo, ScpExec
exec_info = ScpExecInfo(hostfile=Hostfile(["remote.host.com"]))
result = ScpExec(["/local/file.txt"], exec_info)

# Factory usage
from jarvis_cd.shell import Exec, ExecType, LocalExecInfo
exec_info = LocalExecInfo()
result = Exec("echo hello", exec_info)
"""

# Core classes
from .exec_info import (
    ExecType, ExecInfo, LocalExecInfo, SshExecInfo, PsshExecInfo,
    MpiExecInfo, ScpExecInfo, PscpExecInfo
)
from ..util.hostfile import Hostfile
from .core_exec import CoreExec, LocalExec, MpiVersion
from .ssh_exec import SshExec, PsshExec
from .mpi_exec import (
    LocalMpiExec, OpenMpiExec, MpichExec, IntelMpiExec,
    CrayMpichExec, MpiExec
)
from .scp_exec import ScpExec, PscpExec
from .exec_factory import Exec
from .process import Kill, KillAll, Which, Mkdir, Rm, Chmod, Sleep, Echo
from .resource_graph_exec import ResourceGraphExec
from .container_compose_exec import (
    PodmanComposeExec, DockerComposeExec, ContainerComposeExec,
    PodmanBuildExec, DockerBuildExec, ContainerBuildExec
)
from .container_exec import (
    PodmanContainerExec, DockerContainerExec, ContainerExec
)

__all__ = [
    # Enums and Info classes
    'ExecType', 'ExecInfo', 'LocalExecInfo', 'SshExecInfo', 'PsshExecInfo',
    'MpiExecInfo', 'ScpExecInfo', 'PscpExecInfo',

    # Core execution
    'Hostfile', 'CoreExec', 'LocalExec', 'MpiVersion',

    # SSH execution
    'SshExec', 'PsshExec',

    # MPI execution
    'LocalMpiExec', 'OpenMpiExec', 'MpichExec', 'IntelMpiExec',
    'CrayMpichExec', 'MpiExec',

    # File transfer
    'ScpExec', 'PscpExec',

    # Factory and utilities
    'Exec', 'Kill', 'KillAll', 'Which', 'Mkdir', 'Rm', 'Chmod', 'Sleep', 'Echo',

    # Resource graph
    'ResourceGraphExec',

    # Container compose
    'PodmanComposeExec', 'DockerComposeExec', 'ContainerComposeExec',
    'PodmanBuildExec', 'DockerBuildExec', 'ContainerBuildExec',

    # Container exec
    'PodmanContainerExec', 'DockerContainerExec', 'ContainerExec'
]