"""
Process utility classes for Jarvis shell execution.
"""
from typing import Union, List
from .core_exec import LocalExec
from .exec_info import ExecInfo


class Kill(LocalExec):
    """
    Kill all processes which match the name regex.
    """
    
    def __init__(self, cmd: str, exec_info: ExecInfo, partial: bool = True):
        """
        Kill all processes which match the name regex.
        
        :param cmd: A regex for the command to kill
        :param exec_info: Info needed to execute the command
        :param partial: If True, use partial matching (-f flag)
        """
        partial_flag = "-f" if partial else ""
        kill_cmd = f"pkill -9 {partial_flag} '{cmd}'"
        super().__init__(kill_cmd, exec_info)
        
    def get_cmd(self) -> str:
        """Get the kill command"""
        return self.cmd


class KillAll(LocalExec):
    """
    Kill all processes owned by the current user.
    """
    
    def __init__(self, exec_info: ExecInfo):
        """
        Kill all processes owned by current user.
        
        :param exec_info: Info needed to execute the command
        """
        kill_cmd = "pkill -9 -u $(whoami)"
        super().__init__(kill_cmd, exec_info)


class Which(LocalExec):
    """
    Find the location of an executable.
    """
    
    def __init__(self, executable: str, exec_info: ExecInfo):
        """
        Find executable location.
        
        :param executable: Name of executable to find
        :param exec_info: Execution information
        """
        which_cmd = f"which {executable}"
        super().__init__(which_cmd, exec_info)
        self.executable = executable
        
    def get_path(self) -> str:
        """
        Get the path to the executable.
        
        :return: Path to executable or empty string if not found
        """
        return self.stdout.get('localhost', '').strip()
        
    def exists(self) -> bool:
        """
        Check if executable exists.
        
        :return: True if executable was found
        """
        return self.exit_code.get('localhost', 1) == 0 and bool(self.get_path())


class Mkdir(LocalExec):
    """
    Create directories.
    """
    
    def __init__(self, paths: Union[str, List[str]], exec_info: ExecInfo, 
                 parents: bool = True, exist_ok: bool = True):
        """
        Create directories.
        
        :param paths: Directory path(s) to create
        :param exec_info: Execution information
        :param parents: Create parent directories if needed
        :param exist_ok: Don't error if directory already exists
        """
        if isinstance(paths, str):
            paths = [paths]
            
        flags = []
        if parents:
            flags.append('-p')
            
        # Build command with properly escaped paths
        flag_str = ' '.join(flags)
        path_str = ' '.join([f'"{path}"' for path in paths])
        mkdir_cmd = f"mkdir {flag_str} {path_str}".strip()
            
        super().__init__(mkdir_cmd, exec_info)


class Rm(LocalExec):
    """
    Remove files and directories.
    """
    
    def __init__(self, paths: Union[str, List[str]], exec_info: ExecInfo,
                 recursive: bool = False, force: bool = True):
        """
        Remove files and directories.
        
        :param paths: File/directory path(s) to remove
        :param exec_info: Execution information
        :param recursive: Remove directories recursively
        :param force: Force removal without prompting
        """
        if isinstance(paths, str):
            paths = [paths]
            
        flags = []
        if recursive:
            flags.append('-r')
        if force:
            flags.append('-f')
            
        # Build command with properly escaped paths
        flag_str = ' '.join(flags)
        path_str = ' '.join([f'"{path}"' for path in paths])
        rm_cmd = f"rm {flag_str} {path_str}".strip()
            
        super().__init__(rm_cmd, exec_info)


class Chmod(LocalExec):
    """
    Change file permissions.
    """
    
    def __init__(self, paths: Union[str, List[str]], mode: str, exec_info: ExecInfo,
                 recursive: bool = False):
        """
        Change file permissions.
        
        :param paths: File/directory path(s) to modify
        :param mode: Permission mode (e.g., '755', '+x', 'u+w')
        :param exec_info: Execution information
        :param recursive: Apply recursively
        """
        if isinstance(paths, str):
            paths = [paths]
            
        flags = []
        if recursive:
            flags.append('-R')
            
        # Build command with properly escaped paths
        flag_str = ' '.join(flags)
        path_str = ' '.join([f'"{path}"' for path in paths])
        chmod_cmd = f"chmod {flag_str} {mode} {path_str}".strip()
            
        super().__init__(chmod_cmd, exec_info)


class Sleep(LocalExec):
    """
    Sleep for a specified duration.
    """
    
    def __init__(self, duration: Union[int, float], exec_info: ExecInfo):
        """
        Sleep for specified duration.
        
        :param duration: Sleep duration in seconds
        :param exec_info: Execution information
        """
        sleep_cmd = f"sleep {duration}"
        super().__init__(sleep_cmd, exec_info)


class Echo(LocalExec):
    """
    Echo text to stdout.
    """
    
    def __init__(self, text: str, exec_info: ExecInfo):
        """
        Echo text to stdout.
        
        :param text: Text to echo
        :param exec_info: Execution information
        """
        echo_cmd = f'echo "{text}"'
        super().__init__(echo_cmd, exec_info)