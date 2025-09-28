"""
Exec factory for Jarvis shell execution.
"""
from .exec_info import ExecInfo, ExecType
from .core_exec import LocalExec
from .ssh_exec import SshExec, PsshExec
from .mpi_exec import MpiExec
from .scp_exec import ScpExec, PscpExec


class Exec:
    """
    Factory class for creating appropriate executor based on ExecInfo type.
    """
    
    def __new__(cls, cmd: str, exec_info: ExecInfo):
        """
        Create appropriate executor based on exec_info type.
        
        :param cmd: Command to execute
        :param exec_info: Execution information
        :return: Appropriate executor instance
        """
        if exec_info.exec_type == ExecType.LOCAL:
            return LocalExec(cmd, exec_info)
        elif exec_info.exec_type == ExecType.SSH:
            return SshExec(cmd, exec_info)
        elif exec_info.exec_type == ExecType.PSSH:
            return PsshExec(cmd, exec_info)
        elif exec_info.exec_type in [ExecType.MPI, ExecType.OPENMPI, 
                                     ExecType.MPICH, ExecType.INTEL_MPI, 
                                     ExecType.CRAY_MPICH]:
            return MpiExec(cmd, exec_info)
        else:
            raise ValueError(f"Unsupported execution type: {exec_info.exec_type}")