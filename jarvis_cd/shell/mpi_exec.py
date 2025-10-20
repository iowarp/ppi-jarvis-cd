"""
MPI execution classes for Jarvis shell execution.
"""
from abc import abstractmethod
from typing import Union, List, Dict, Any
from .core_exec import LocalExec, MpiVersion
from .exec_info import ExecInfo, MpiExecInfo, ExecType
from ..util.hostfile import Hostfile


class LocalMpiExec(LocalExec):
    """
    Base class used by all MPI implementations.
    """

    def __init__(self, cmd: Union[str, List[Dict[str, Any]]], exec_info: MpiExecInfo):
        """
        Initialize MPI execution.

        :param cmd: Command to execute with MPI. Can be:
                   - A string: single command
                   - A list of dicts: multiple commands with format:
                     [{'cmd': str, 'nprocs': int, 'disable_preload': bool (optional)}, ...]
                     If 'disable_preload' is True, LD_PRELOAD will be removed for that command
        :param exec_info: MPI execution information
        """
        self.nprocs = exec_info.nprocs
        self.ppn = exec_info.ppn
        self.hostfile = exec_info.hostfile or Hostfile(['localhost'])
        self.mpi_env = exec_info.env
        self.ssh_port = exec_info.port if exec_info.port else None

        # Process command format
        if isinstance(cmd, str):
            # Single command format
            self.original_cmd = cmd
            self.cmd_list = None
        else:
            # Multi-command format: list of dicts
            self.cmd_list = self._process_cmd_list(cmd)
            self.original_cmd = None

        # Build MPI command
        mpi_cmd = self.mpicmd()

        # Create modified exec_info for LocalExec
        local_info = exec_info.mod(
            env=exec_info.basic_env
        )

        super().__init__(mpi_cmd, local_info)

    def _process_cmd_list(self, cmd_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process list of command dicts, calculating final nprocs for each.

        :param cmd_list: List of dicts with 'cmd', 'nprocs', and optional 'disable_preload' keys
        :return: Processed list with calculated nprocs and environment settings
        """
        if not cmd_list:
            raise ValueError("Command list cannot be empty")

        processed = []
        total_nprocs_allocated = 0

        # Process all but the last command
        for i, cmd_dict in enumerate(cmd_list[:-1]):
            nprocs = cmd_dict.get('nprocs', 0)
            processed.append({
                'cmd': cmd_dict['cmd'],
                'nprocs': nprocs,
                'disable_preload': cmd_dict.get('disable_preload', False)
            })
            total_nprocs_allocated += nprocs

        # Process last command - calculate remaining nprocs
        last_cmd = cmd_list[-1]
        remaining_nprocs = self.nprocs - total_nprocs_allocated

        if remaining_nprocs < 0:
            raise ValueError(f"Total nprocs ({total_nprocs_allocated}) exceeds available ({self.nprocs})")

        processed.append({
            'cmd': last_cmd['cmd'],
            'nprocs': remaining_nprocs,
            'disable_preload': last_cmd.get('disable_preload', False)
        })

        return processed

    @abstractmethod
    def mpicmd(self) -> str:
        """Build MPI command. Must be implemented by subclasses."""
        pass


class OpenMpiExec(LocalMpiExec):
    """
    Execute commands using OpenMPI.
    """

    def mpicmd(self) -> str:
        """Build OpenMPI command"""
        params = ['mpiexec']
        params.append('--oversubscribe')
        params.append('--allow-run-as-root')  # For docker

        # Set SSH port if explicitly specified (SSH config will be used otherwise)
        if self.ssh_port and self.ssh_port != 22:
            params.append(f'--mca plm_rsh_args "-p {self.ssh_port}"')

        if self.ppn is not None:
            params.append(f'-npernode {self.ppn}')

        if len(self.hostfile):
            if self.hostfile.path is None:
                params.append(f'--host {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')

        # Handle multi-command format
        if self.cmd_list:
            cmd_parts = []
            for cmd_dict in self.cmd_list:
                nprocs = cmd_dict['nprocs']
                cmd = cmd_dict['cmd']
                disable_preload = cmd_dict.get('disable_preload', False)

                # Skip commands with 0 nprocs
                if nprocs > 0:
                    # Build per-command environment variables
                    cmd_env = self.mpi_env.copy()
                    if disable_preload and 'LD_PRELOAD' in cmd_env:
                        del cmd_env['LD_PRELOAD']

                    # Add environment variables for this command
                    env_args = ' '.join([f'-x {key}="{val}"' for key, val in cmd_env.items()])
                    cmd_parts.append(f'{env_args} -n {nprocs} {cmd}')
            # Join with ' : ' for multiple commands
            params.append(' : '.join(cmd_parts))
        else:
            # Single command format - add global environment variables
            params.extend([f'-x {key}="{val}"' for key, val in self.mpi_env.items()])
            params.append(f'-n {self.nprocs}')
            params.append(self.original_cmd)

        return ' '.join(params)


class MpichExec(LocalMpiExec):
    """
    Execute commands using MPICH.
    """

    def mpicmd(self) -> str:
        """Build MPICH command"""
        params = ['mpiexec']

        # Set SSH port if explicitly specified (SSH config will be used otherwise)
        if self.ssh_port and self.ssh_port != 22:
            params.append(f'-bootstrap-exec-args "-p {self.ssh_port}"')

        if self.ppn is not None:
            params.append(f'-ppn {self.ppn}')

        if len(self.hostfile):
            if self.hostfile.path is None:
                params.append(f'--host {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')

        # Handle multi-command format
        if self.cmd_list:
            cmd_parts = []
            for cmd_dict in self.cmd_list:
                nprocs = cmd_dict['nprocs']
                cmd = cmd_dict['cmd']
                disable_preload = cmd_dict.get('disable_preload', False)

                # Skip commands with 0 nprocs
                if nprocs > 0:
                    # Build per-command environment variables
                    cmd_env = self.mpi_env.copy()
                    if disable_preload and 'LD_PRELOAD' in cmd_env:
                        del cmd_env['LD_PRELOAD']

                    # Add environment variables for this command
                    env_args = ' '.join([f'-env {key}="{val}"' for key, val in cmd_env.items()])
                    cmd_parts.append(f'{env_args} -n {nprocs} {cmd}')
            # Join with ' : ' for multiple commands
            params.append(' : '.join(cmd_parts))
        else:
            # Single command format - add global environment variables
            params.extend([f'-genv {key}="{val}"' for key, val in self.mpi_env.items()])
            params.append(f'-n {self.nprocs}')
            params.append(self.original_cmd)

        return ' '.join(params)


class IntelMpiExec(MpichExec):
    """
    Execute commands using Intel MPI (similar to MPICH).
    """
    pass


class CrayMpichExec(LocalMpiExec):
    """
    Execute commands using Cray MPICH.
    """

    def mpicmd(self) -> str:
        """Build Cray MPICH command"""
        params = ['mpiexec']

        if self.ppn is not None:
            params.append(f'--ppn {self.ppn}')

        if len(self.hostfile):
            if (self.hostfile.hosts[0] == 'localhost' and
                len(self.hostfile) == 1):
                pass  # Skip hostfile for localhost-only
            elif self.hostfile.path is None:
                params.append(f'--hosts {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')

        # Handle multi-command format
        if self.cmd_list:
            cmd_parts = []
            for cmd_dict in self.cmd_list:
                nprocs = cmd_dict['nprocs']
                cmd = cmd_dict['cmd']
                disable_preload = cmd_dict.get('disable_preload', False)

                # Skip commands with 0 nprocs
                if nprocs > 0:
                    # Build per-command environment variables
                    cmd_env = self.mpi_env.copy()
                    if disable_preload and 'LD_PRELOAD' in cmd_env:
                        del cmd_env['LD_PRELOAD']

                    # Add environment variables for this command
                    env_args = ' '.join([f'--env {key}="{val}"' for key, val in cmd_env.items()])
                    cmd_parts.append(f'{env_args} -n {nprocs} {cmd}')
            # Join with ' : ' for multiple commands
            params.append(' : '.join(cmd_parts))
        else:
            # Single command format - add global environment variables
            params.extend([f'--env {key}="{val}"' for key, val in self.mpi_env.items()])
            params.append(f'-n {self.nprocs}')
            params.append(self.original_cmd)

        return ' '.join(params)


class MpiExec:
    """
    Factory class for MPI execution that automatically detects MPI implementation.
    """

    def __new__(cls, cmd: Union[str, List[Dict[str, Any]]], exec_info: MpiExecInfo):
        """
        Create appropriate MPI executor based on detected MPI implementation.

        :param cmd: Command to execute. Can be:
                   - A string: single command
                   - A list of dicts: multiple commands with format [{'cmd': str, 'nprocs': int}, ...]
        :param exec_info: MPI execution information
        :return: Appropriate MPI executor instance
        """
        # Detect MPI version
        mpi_version_detector = MpiVersion(exec_info)
        mpi_type = mpi_version_detector.version
        
        # Create appropriate executor
        if mpi_type == ExecType.OPENMPI:
            return OpenMpiExec(cmd, exec_info)
        elif mpi_type == ExecType.MPICH:
            return MpichExec(cmd, exec_info)
        elif mpi_type == ExecType.INTEL_MPI:
            return IntelMpiExec(cmd, exec_info)
        elif mpi_type == ExecType.CRAY_MPICH:
            return CrayMpichExec(cmd, exec_info)
        else:
            # Default to MPICH
            print(f"Unknown MPI type {mpi_type}, defaulting to MPICH")
            return MpichExec(cmd, exec_info)