"""
MPI execution classes for Jarvis shell execution.
"""
from abc import abstractmethod
from .core_exec import LocalExec, MpiVersion
from .exec_info import ExecInfo, MpiExecInfo, ExecType
from ..util.hostfile import Hostfile


class LocalMpiExec(LocalExec):
    """
    Base class used by all MPI implementations.
    """
    
    def __init__(self, cmd: str, exec_info: MpiExecInfo):
        """
        Initialize MPI execution.
        
        :param cmd: Command to execute with MPI
        :param exec_info: MPI execution information
        """
        self.original_cmd = cmd
        self.nprocs = exec_info.nprocs
        self.ppn = exec_info.ppn
        self.hostfile = exec_info.hostfile or Hostfile(['localhost'])
        self.mpi_env = exec_info.env
        
        # Handle debugging
        if exec_info.do_dbg:
            self.base_cmd = cmd  # Store original for additional processes
            cmd = self.get_dbg_cmd(cmd, exec_info)
            
        # Build MPI command
        mpi_cmd = self.mpicmd()
        
        # Create modified exec_info for LocalExec
        local_info = exec_info.mod(
            env=exec_info.basic_env,
            do_dbg=False
        )
        
        super().__init__(mpi_cmd, local_info)
        
    def get_dbg_cmd(self, cmd: str, exec_info: MpiExecInfo) -> str:
        """
        Build debug command for gdbserver.
        
        :param cmd: Original command
        :param exec_info: MPI execution information
        :return: Debug command
        """
        return f"gdbserver localhost:{exec_info.dbg_port} {cmd}"
        
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
        
        if self.ppn is not None:
            params.append(f'-npernode {self.ppn}')
            
        if len(self.hostfile):
            if self.hostfile.path is None:
                params.append(f'--host {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')
                
        # Add environment variables
        params.extend([f'-x {key}="{val}"' for key, val in self.mpi_env.items()])
        
        # Handle debugging
        if self.original_cmd.startswith('gdbserver'):
            params.append(f'-n 1 {self.original_cmd}')
            if self.nprocs > 1:
                params.append(f': -n {self.nprocs - 1} {self.base_cmd}')
        else:
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
        
        if self.ppn is not None:
            params.append(f'-ppn {self.ppn}')
            
        if len(self.hostfile):
            if self.hostfile.path is None:
                params.append(f'--host {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')
                
        # Add environment variables
        params.extend([f'-genv {key}="{val}"' for key, val in self.mpi_env.items()])
        
        # Handle debugging
        if self.original_cmd.startswith('gdbserver'):
            params.append(f'-n 1 {self.original_cmd}')
            if self.nprocs > 1:
                params.append(f': -n {self.nprocs - 1} {self.base_cmd}')
        else:
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
        params = [f'mpiexec -n {self.nprocs}']
        
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
                
        # Add environment variables
        params.extend([f'--env {key}="{val}"' for key, val in self.mpi_env.items()])
        
        params.append(self.original_cmd)
        
        return ' '.join(params)


class MpiExec:
    """
    Factory class for MPI execution that automatically detects MPI implementation.
    """
    
    def __new__(cls, cmd: str, exec_info: MpiExecInfo):
        """
        Create appropriate MPI executor based on detected MPI implementation.
        
        :param cmd: Command to execute
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