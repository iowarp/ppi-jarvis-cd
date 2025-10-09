"""
SCP/file transfer execution classes for Jarvis shell execution.
"""
import os
import threading
from typing import List, Union, Tuple, Dict
from pathlib import Path

from .core_exec import CoreExec, LocalExec
from .exec_info import ScpExecInfo, PscpExecInfo
from ..util.hostfile import Hostfile


class _Scp(LocalExec):
    """
    Internal SCP class for copying files using rsync.
    """
    
    def __init__(self, src_path: str, dst_path: str, exec_info: ScpExecInfo):
        """
        Copy a file or directory from source to destination via rsync.
        
        :param src_path: The path to the file on the host
        :param dst_path: The desired file path on the remote host
        :param exec_info: Info needed to execute command with SSH
        """
        if not exec_info.hostfile or len(exec_info.hostfile) == 0:
            raise ValueError("SCP requires a hostfile with at least one host")
            
        self.addr = exec_info.hostfile.hosts[0]
        
        # Skip if copying to localhost
        if self.addr in ['localhost', '127.0.0.1']:
            # For localhost, just do a local copy if paths are different
            if src_path != dst_path:
                super().__init__(f'cp -r "{src_path}" "{dst_path}"', exec_info)
            else:
                # Same path on localhost - no operation needed
                super().__init__('true', exec_info)  # No-op command
            return
            
        self.src_path = src_path
        self.dst_path = dst_path
        self.user = exec_info.user
        self.pkey = exec_info.pkey
        self.port = exec_info.port
        self.sudo = exec_info.sudo
        
        # Build rsync command
        rsync_cmd = self.build_rsync_cmd(src_path, dst_path)
        
        # Create modified exec_info for LocalExec
        local_info = exec_info.mod(env=exec_info.basic_env)
        
        super().__init__(rsync_cmd, local_info)
        
    def build_rsync_cmd(self, src_path: str, dst_path: str) -> str:
        """
        Build rsync command for file transfer.
        
        :param src_path: Source path
        :param dst_path: Destination path
        :return: Complete rsync command
        """
        lines = ['rsync -ha']
        
        # Add SSH options if needed
        if self.pkey is not None or self.port is not None:
            ssh_lines = ['ssh']
            if self.pkey is not None:
                ssh_lines.append(f'-i {self.pkey}')
            if self.port is not None and self.port != 22:
                ssh_lines.append(f'-p {self.port}')
            ssh_cmd = ' '.join(ssh_lines)
            lines.append(f'-e \'{ssh_cmd}\'')
            
        # Add source path
        lines.append(f'"{src_path}"')
        
        # Add destination
        if self.user is not None:
            lines.append(f'"{self.user}@{self.addr}:{dst_path}"')
        else:
            lines.append(f'"{self.addr}:{dst_path}"')
            
        return ' '.join(lines)


class ScpExec(CoreExec):
    """
    Secure copy data between hosts using rsync.
    """
    
    def __init__(self, paths: Union[str, List[str], List[Tuple[str, str]]], 
                 exec_info: ScpExecInfo):
        """
        Copy files via rsync.
        
        Case 1: Paths is a single file:
        paths = '/tmp/hi.txt'
        '/tmp/hi.txt' will be copied to user@host:/tmp/hi.txt
        
        Case 2: Paths is a list of files:
        paths = ['/tmp/hi1.txt', '/tmp/hi2.txt']
        Repeat Case 1 twice.
        
        Case 3: Paths is a list of tuples of files:
        paths = [('/tmp/hi.txt', '/tmp/remote_hi.txt')]
        '/tmp/hi.txt' will be copied to user@host:'/tmp/remote_hi.txt'
        
        :param paths: Either a path to a file, a list of files, or a list of
        tuples of files.
        :param exec_info: Connection information for SSH
        """
        super().__init__()
        self.paths = paths
        self.exec_info = exec_info
        self.scp_nodes = []
        
        # Determine which execution pattern to use
        if isinstance(paths, str):
            self._exec_single_path(paths)
        elif isinstance(paths, list):
            if len(paths) == 0:
                raise ValueError('Must have at least one path to scp')
            elif isinstance(paths[0], str):
                self._exec_many_paths(paths)
            elif isinstance(paths[0], (tuple, list)):
                self._exec_many_paths_tuple(paths)
        else:
            raise ValueError(f"Invalid paths type: {type(paths)}")
            
        # If not async, wait for completion
        if not self.exec_info.exec_async:
            self.wait_all_scp()
            
    def _exec_single_path(self, path: str):
        """Execute SCP for a single path"""
        self.scp_nodes.append(_Scp(path, path, self.exec_info))
        
    def _exec_many_paths(self, paths: List[str]):
        """Execute SCP for multiple paths (same src and dst names)"""
        for path in paths:
            self.scp_nodes.append(_Scp(path, path, self.exec_info))
            
    def _exec_many_paths_tuple(self, path_tlist: List[Tuple[str, str]]):
        """Execute SCP for list of (src, dst) tuples"""
        for src, dst in path_tlist:
            self.scp_nodes.append(_Scp(src, dst, self.exec_info))

    def run(self):
        """Execute SCP operations (already done in __init__)"""
        # SCP operations are started in __init__ via _exec_* methods
        pass

    def wait_all_scp(self) -> Dict[str, int]:
        """
        Wait for all SCP operations to complete.
        
        :return: Dictionary of exit codes
        """
        self.wait_list(self.scp_nodes)
        self.smash_list_outputs(self.scp_nodes)
        self.set_exit_code()
        return self.exit_code
        
    def wait_list(self, exec_list: List[_Scp]):
        """Wait for a list of executors to complete"""
        for executor in exec_list:
            executor.wait_all()
            
    def smash_list_outputs(self, exec_list: List[_Scp]):
        """Combine outputs from multiple executors"""
        for executor in exec_list:
            for hostname in executor.stdout:
                if hostname not in self.stdout:
                    self.stdout[hostname] = ""
                self.stdout[hostname] += executor.stdout[hostname]
                
            for hostname in executor.stderr:
                if hostname not in self.stderr:
                    self.stderr[hostname] = ""
                self.stderr[hostname] += executor.stderr[hostname]
                
    def set_exit_code(self):
        """Set exit code based on SCP operations"""
        self.set_exit_code_list(self.scp_nodes)
        
    def set_exit_code_list(self, exec_list: List[_Scp]):
        """Set exit code from a list of executors"""
        for executor in exec_list:
            for hostname in executor.exit_code:
                # Use the highest (worst) exit code
                current_code = self.exit_code.get(hostname, 0)
                new_code = executor.exit_code[hostname]
                self.exit_code[hostname] = max(current_code, new_code)
                
    def get_cmd(self) -> str:
        """Get description of SCP operation"""
        if isinstance(self.paths, str):
            return f"scp {self.paths}"
        elif isinstance(self.paths, list):
            if len(self.paths) == 1:
                if isinstance(self.paths[0], str):
                    return f"scp {self.paths[0]}"
                else:
                    return f"scp {self.paths[0][0]} -> {self.paths[0][1]}"
            else:
                return f"scp {len(self.paths)} files"
        return "scp operation"


class PscpExec(CoreExec):
    """
    Parallel SCP execution across multiple hosts.
    """
    
    def __init__(self, paths: Union[str, List[str], List[Tuple[str, str]]], 
                 exec_info: PscpExecInfo):
        """
        Copy files to multiple hosts in parallel.
        
        :param paths: Paths to copy (same format as ScpExec)
        :param exec_info: Parallel SCP execution information
        """
        super().__init__()
        self.paths = paths
        self.exec_info = exec_info
        self.scp_executors = {}
        
        if not exec_info.hostfile or len(exec_info.hostfile) == 0:
            raise ValueError("PSCP requires a hostfile with at least one host")
            
        # Start SCP on each host
        self.run()
        
        # If not async, wait for all to complete
        if not exec_info.exec_async:
            self.wait_all()
            
    def run(self):
        """Execute SCP on all hosts in parallel"""
        threads = []
        
        for hostname in self.exec_info.hostfile.hosts:
            # Create single-host hostfile for this SCP operation
            host_hostfile = Hostfile(hosts=[hostname], find_ips=False)
            
            # Create SCP exec info for this host
            scp_info = ScpExecInfo(
                user=self.exec_info.user,
                pkey=self.exec_info.pkey,
                port=self.exec_info.port,
                hostfile=host_hostfile,
                env=self.exec_info.env,
                sudo=self.exec_info.sudo,
                sudoenv=self.exec_info.sudoenv,
                cwd=self.exec_info.cwd,
                collect_output=self.exec_info.collect_output,
                pipe_stdout=self.exec_info.pipe_stdout,
                pipe_stderr=self.exec_info.pipe_stderr,
                hide_output=self.exec_info.hide_output,
                exec_async=True,  # Always async for parallel execution
                strict_ssh=self.exec_info.strict_ssh,
                timeout=self.exec_info.timeout
            )
            
            # Start SCP execution in a thread
            thread = threading.Thread(
                target=self._execute_on_host,
                args=(hostname, scp_info)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
        # Wait for all threads to start their SCP processes
        for thread in threads:
            thread.join()
            
    def _execute_on_host(self, hostname: str, scp_info: ScpExecInfo):
        """
        Execute SCP on a specific host.
        
        :param hostname: Target hostname
        :param scp_info: SCP execution information
        """
        try:
            scp_exec = ScpExec(self.paths, scp_info)
            self.scp_executors[hostname] = scp_exec
            
        except Exception as e:
            print(f"Error executing SCP on {hostname}: {e}")
            self.exit_code[hostname] = 1
            self.stdout[hostname] = ""
            self.stderr[hostname] = str(e)
            
    def wait(self, hostname: str) -> int:
        """
        Wait for SCP on a specific host to complete.
        
        :param hostname: Hostname to wait for
        :return: Exit code
        """
        if hostname in self.scp_executors:
            scp_exec = self.scp_executors[hostname]
            exit_codes = scp_exec.wait_all_scp()
            
            # Copy outputs (SCP uses localhost as key)
            self.stdout[hostname] = scp_exec.stdout.get('localhost', "")
            self.stderr[hostname] = scp_exec.stderr.get('localhost', "")
            self.exit_code[hostname] = exit_codes.get('localhost', 0)
            
            return self.exit_code[hostname]
        return 0
        
    def get_cmd(self) -> str:
        """Get description of parallel SCP operation"""
        return f"pscp to {len(self.exec_info.hostfile.hosts)} hosts"