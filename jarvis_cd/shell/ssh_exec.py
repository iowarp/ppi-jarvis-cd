"""
SSH execution classes for Jarvis shell execution.
"""
import threading
from typing import List, Dict, Any
from .core_exec import CoreExec, LocalExec
from .exec_info import ExecInfo, SshExecInfo, PsshExecInfo
from ..util.hostfile import Hostfile


class SshExec(LocalExec):
    """
    Execute commands on remote hosts using SSH.
    Inherits from LocalExec to reuse subprocess management.
    """
    
    def __init__(self, cmd: str, exec_info: SshExecInfo, hostname: str = None):
        """
        Initialize SSH execution.
        
        :param cmd: Command to execute remotely
        :param exec_info: SSH execution information
        :param hostname: Target hostname (if None, uses first host from hostfile)
        """
        self.original_cmd = cmd
        self.target_hostname = hostname or (exec_info.hostfile.hosts[0] if exec_info.hostfile else 'localhost')
        
        # Build SSH command
        ssh_cmd = self._build_ssh_command(cmd, exec_info)
        
        # Initialize with SSH command
        super().__init__(ssh_cmd, exec_info)
        
        # Override hostname for output tracking
        self.hostname = self.target_hostname
        if 'localhost' in self.stdout:
            self.stdout[self.hostname] = self.stdout.pop('localhost')
        if 'localhost' in self.stderr:
            self.stderr[self.hostname] = self.stderr.pop('localhost')
        if 'localhost' in self.exit_code:
            self.exit_code[self.hostname] = self.exit_code.pop('localhost')
        if 'localhost' in self.processes:
            self.processes[self.hostname] = self.processes.pop('localhost')
        if 'localhost' in self.output_threads:
            self.output_threads[self.hostname] = self.output_threads.pop('localhost')
            
    def _build_ssh_command(self, cmd: str, exec_info: SshExecInfo) -> str:
        """
        Build SSH command with all necessary parameters.
        
        :param cmd: Original command to execute
        :param exec_info: SSH execution information
        :return: Complete SSH command string
        """
        ssh_parts = ['ssh']
        
        # SSH options
        if not exec_info.strict_ssh:
            ssh_parts.extend([
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null'
            ])
            
        # Port
        if exec_info.port and exec_info.port != 22:
            ssh_parts.extend(['-p', str(exec_info.port)])
            
        # Private key
        if exec_info.pkey:
            ssh_parts.extend(['-i', exec_info.pkey])
            
        # Connection timeout
        if exec_info.timeout:
            ssh_parts.extend(['-o', f'ConnectTimeout={exec_info.timeout}'])
            
        # Target host
        if exec_info.user:
            ssh_parts.append(f'{exec_info.user}@{self.target_hostname}')
        else:
            ssh_parts.append(self.target_hostname)
            
        # Build remote command
        remote_cmd = self._build_remote_command(cmd, exec_info)
        ssh_parts.append(f"'{remote_cmd}'")
        
        return ' '.join(ssh_parts)
        
    def _build_remote_command(self, cmd: str, exec_info: SshExecInfo) -> str:
        """
        Build the command to execute on the remote host.

        :param cmd: Original command
        :param exec_info: SSH execution information
        :return: Remote command string
        """
        cmd_parts = []
        env_prefix = []

        # Change directory if specified (must use && since it's a separate command)
        if exec_info.cwd:
            cmd_parts.append(f'cd {exec_info.cwd}')

        # Set environment variables (these go before the command on same line)
        if exec_info.env:
            for key, value in exec_info.env.items():
                # Escape special characters in environment values
                # Use double quotes to allow spaces, and escape internal double quotes
                escaped_value = str(value).replace('"', '\\"')
                env_prefix.append(f'{key}="{escaped_value}"')

        # Build the final command with env vars, sudo, and the actual command
        final_cmd_parts = []

        # Add environment variables
        if env_prefix:
            final_cmd_parts.append(' '.join(env_prefix))

        # Add sudo if requested
        if exec_info.sudo:
            if exec_info.sudoenv and exec_info.env:
                # Preserve environment with sudo
                final_cmd_parts.append('sudo -E')
            else:
                final_cmd_parts.append('sudo')

        # Add the actual command
        final_cmd_parts.append(cmd)

        # Join env vars, sudo, and command with spaces (they run together)
        final_cmd = ' '.join(final_cmd_parts)

        # Add cd command if needed (joined with &&)
        if cmd_parts:
            cmd_parts.append(final_cmd)
            return ' && '.join(cmd_parts)
        else:
            return final_cmd


class PsshExec(CoreExec):
    """
    Execute commands on multiple hosts using parallel SSH.
    """
    
    def __init__(self, cmd: str, exec_info: PsshExecInfo):
        """
        Initialize parallel SSH execution.
        
        :param cmd: Command to execute on all hosts
        :param exec_info: PSSH execution information
        """
        super().__init__()
        self.cmd = cmd
        self.exec_info = exec_info
        self.ssh_executors = {}
        
        if not exec_info.hostfile or len(exec_info.hostfile) == 0:
            raise ValueError("PSSH requires a hostfile with at least one host")
            
        # Start SSH execution on each host
        self.run()
        
        # If not async, wait for all to complete
        if not exec_info.exec_async:
            self.wait_all()
            
    def run(self):
        """Execute command on all hosts in parallel"""
        threads = []
        
        for hostname in self.exec_info.hostfile.hosts:
            # Create SSH exec info for this host
            ssh_info = SshExecInfo(
                user=self.exec_info.user,
                pkey=self.exec_info.pkey,
                port=self.exec_info.port,
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
            
            # Start SSH execution in a thread
            thread = threading.Thread(
                target=self._execute_on_host,
                args=(hostname, ssh_info)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
        # Wait for all threads to start their SSH processes
        for thread in threads:
            thread.join()
            
    def _execute_on_host(self, hostname: str, ssh_info: SshExecInfo):
        """
        Execute command on a specific host.
        
        :param hostname: Target hostname
        :param ssh_info: SSH execution information
        """
        try:
            ssh_exec = SshExec(self.cmd, ssh_info, hostname)
            self.ssh_executors[hostname] = ssh_exec
            
            # Copy process reference for management
            if hostname in ssh_exec.processes:
                self.processes[hostname] = ssh_exec.processes[hostname]
                
        except Exception as e:
            print(f"Error executing on {hostname}: {e}")
            self.exit_code[hostname] = 1
            self.stdout[hostname] = ""
            self.stderr[hostname] = str(e)
            
    def wait(self, hostname: str) -> int:
        """
        Wait for execution on a specific host to complete.
        
        :param hostname: Hostname to wait for
        :return: Exit code
        """
        if hostname in self.ssh_executors:
            ssh_exec = self.ssh_executors[hostname]
            exit_code = ssh_exec.wait(hostname)
            
            # Copy outputs
            self.stdout[hostname] = ssh_exec.stdout.get(hostname, "")
            self.stderr[hostname] = ssh_exec.stderr.get(hostname, "")
            self.exit_code[hostname] = exit_code
            
            return exit_code
        return 0
        
    def get_cmd(self) -> str:
        """Get the original command"""
        return self.cmd