"""
Execution information classes for Jarvis shell execution.
Contains ExecType enums and ExecInfo data structures.
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pathlib import Path


class ExecType(Enum):
    """Execution types supported by Jarvis"""
    LOCAL = "local"
    SSH = "ssh"
    PSSH = "pssh"
    MPI = "mpi"
    OPENMPI = "openmpi"
    MPICH = "mpich"
    INTEL_MPI = "intel_mpi"
    CRAY_MPICH = "cray_mpich"
    SCP = "scp"
    PSCP = "pscp"


class ExecInfo:
    """
    Contains all information needed to execute a program. This includes
    parameters such as the path to key-pairs, the hosts to run the program
    on, number of processes, etc.
    """
    
    def __init__(self, exec_type=ExecType.LOCAL, nprocs=None, ppn=None,
                 user=None, pkey=None, port=None,
                 hostfile=None, env=None,
                 sleep_ms=0, sudo=False, sudoenv=True, cwd=None,
                 collect_output=None, pipe_stdout=None, pipe_stderr=None,
                 hide_output=None, exec_async=False, stdin=None,
                 strict_ssh=False, timeout=None, **kwargs):
        """
        Initialize execution information.

        :param exec_type: How to execute a program. SSH, MPI, Local, etc.
        :param nprocs: Number of processes to spawn. E.g., MPI uses this
        :param ppn: Number of processes per node. E.g., MPI uses this
        :param user: The user to execute command under. E.g., SSH, PSSH
        :param pkey: The path to the private key. E.g., SSH, PSSH
        :param port: The port to use for connection. E.g., SSH, PSSH
        :param hostfile: The hosts to launch command on. E.g., PSSH, MPI
        :param env: The environment variables to use for command.
        :param sleep_ms: Sleep for a period of time AFTER executing
        :param sudo: Execute command with root privilege. E.g., SSH, PSSH
        :param sudoenv: Support environment preservation in sudo
        :param cwd: Set current working directory. E.g., SSH, PSSH
        :param collect_output: Collect program output in python buffer
        :param pipe_stdout: Pipe STDOUT into a file. (path string)
        :param pipe_stderr: Pipe STDERR into a file. (path string)
        :param hide_output: Whether to print output to console
        :param exec_async: Whether to execute program asynchronously
        :param stdin: Any input needed by the program. Only local
        :param strict_ssh: Strict ssh host key verification
        :param timeout: Timeout subprocess within timeframe
        :param kwargs: Additional unknown parameters (silently ignored)
        """
        self.exec_type = exec_type
        self.nprocs = nprocs or 1
        self.ppn = ppn
        self.user = user
        self.pkey = pkey
        self.port = port or 22
        self.hostfile = hostfile
        self.env = env or {}
        self.sleep_ms = sleep_ms
        self.sudo = sudo
        self.sudoenv = sudoenv
        self.cwd = cwd
        self.collect_output = collect_output if collect_output is not None else True
        self.pipe_stdout = pipe_stdout
        self.pipe_stderr = pipe_stderr
        self.hide_output = hide_output if hide_output is not None else False
        self.exec_async = exec_async
        self.stdin = stdin
        self.strict_ssh = strict_ssh
        self.timeout = timeout

        # Basic environment for process execution (without LD_PRELOAD)
        # This is used for launching MPI itself, not the MPI processes
        self.basic_env = self.env.copy()
        if 'LD_PRELOAD' in self.basic_env:
            del self.basic_env['LD_PRELOAD']
        
    def mod(self, **kwargs):
        """
        Create a modified copy of this ExecInfo with updated parameters.

        :param kwargs: Parameters to modify
        :return: New ExecInfo instance with modifications
        """
        # Create a copy of current attributes
        current_attrs = {}
        for attr in ['exec_type', 'nprocs', 'ppn', 'user', 'pkey', 'port',
                     'hostfile', 'env', 'sleep_ms', 'sudo', 'sudoenv', 'cwd',
                     'collect_output', 'pipe_stdout', 'pipe_stderr', 'hide_output',
                     'exec_async', 'stdin', 'strict_ssh', 'timeout']:
            current_attrs[attr] = getattr(self, attr)

        # Update with new values
        current_attrs.update(kwargs)

        return ExecInfo(**current_attrs)


class SshExecInfo(ExecInfo):
    """SSH-specific execution information"""
    
    def __init__(self, **kwargs):
        super().__init__(exec_type=ExecType.SSH, **kwargs)


class PsshExecInfo(ExecInfo):
    """PSSH-specific execution information"""
    
    def __init__(self, **kwargs):
        super().__init__(exec_type=ExecType.PSSH, **kwargs)


class MpiExecInfo(ExecInfo):
    """MPI-specific execution information"""
    
    def __init__(self, **kwargs):
        super().__init__(exec_type=ExecType.MPI, **kwargs)


class LocalExecInfo(ExecInfo):
    """Local execution information"""
    
    def __init__(self, **kwargs):
        super().__init__(exec_type=ExecType.LOCAL, **kwargs)


class ScpExecInfo(ExecInfo):
    """SCP-specific execution information"""
    
    def __init__(self, **kwargs):
        super().__init__(exec_type=ExecType.SCP, **kwargs)


class PscpExecInfo(ExecInfo):
    """PSCP-specific execution information"""
    
    def __init__(self, **kwargs):
        super().__init__(exec_type=ExecType.PSCP, **kwargs)