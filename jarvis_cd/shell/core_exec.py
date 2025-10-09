"""
Core execution classes for Jarvis shell execution.
"""
import subprocess
import threading
import time
import os
import signal
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

from .exec_info import ExecInfo, ExecType
from ..util.hostfile import Hostfile


class CoreExec(ABC):
    """
    An abstract class representing a class which is intended to run
    shell commands. This includes SSH, MPI, etc.
    """

    def __init__(self):
        self.exit_code = {}  # hostname -> exit_code
        self.stdout = {}     # hostname -> stdout 
        self.stderr = {}     # hostname -> stderr
        self.processes = {}  # hostname -> process
        self.output_threads = {}  # hostname -> (stdout_thread, stderr_thread)
        
    @abstractmethod
    def run(self):
        """Execute the command"""
        pass

    @abstractmethod
    def get_cmd(self) -> str:
        """Get the command string"""
        pass
        
    def wait(self, hostname: str = 'localhost') -> int:
        """
        Wait for execution to complete.
        
        :param hostname: Hostname to wait for
        :return: Exit code
        """
        if hostname in self.processes:
            process = self.processes[hostname]
            exit_code = process.wait()
            self.exit_code[hostname] = exit_code
            
            # Wait for output threads to complete
            if hostname in self.output_threads:
                stdout_thread, stderr_thread = self.output_threads[hostname]
                if stdout_thread:
                    stdout_thread.join()
                if stderr_thread:
                    stderr_thread.join()
                    
            return exit_code
        return 0
        
    def wait_all(self) -> Dict[str, int]:
        """
        Wait for all processes to complete.
        
        :return: Dictionary of hostname -> exit_code
        """
        for hostname in list(self.processes.keys()):
            self.wait(hostname)
        return self.exit_code.copy()
        
    def kill(self, hostname: str = 'localhost'):
        """
        Kill the process.
        
        :param hostname: Hostname to kill process on
        """
        if hostname in self.processes:
            process = self.processes[hostname]
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    # Give it a moment to terminate gracefully
                    time.sleep(0.1)
                    if process.poll() is None:
                        process.kill()
            except ProcessLookupError:
                # Process already terminated
                pass
                
    def kill_all(self):
        """Kill all processes"""
        for hostname in list(self.processes.keys()):
            self.kill(hostname)


class LocalExec(CoreExec):
    """
    Execute commands locally using subprocess.
    """
    
    def __init__(self, cmd: str, exec_info: ExecInfo):
        """
        Initialize local execution.
        
        :param cmd: Command to execute
        :param exec_info: Execution information
        """
        super().__init__()
        self.cmd = cmd
        self.exec_info = exec_info
        self.hostname = 'localhost'
        
        # Initialize output storage
        self.stdout[self.hostname] = ""
        self.stderr[self.hostname] = ""
        self.exit_code[self.hostname] = 0
        
        # Run the command
        self.run()
        
        # If not async, wait for completion
        if not exec_info.exec_async:
            self.wait(self.hostname)
            
    def get_cmd(self) -> str:
        """Get the command string"""
        return self.cmd
        
    def run(self):
        """Execute the command locally"""
        # Set up environment
        if self.exec_info.env:
            env = os.environ.copy()
            # Convert all env values to strings
            for key, value in self.exec_info.env.items():
                env[key] = str(value)
        else:
            env = os.environ
        
        # Prepare stdin
        stdin_pipe = subprocess.PIPE if self.exec_info.stdin else None
        
        # Start process
        try:
            process = subprocess.Popen(
                self.cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=stdin_pipe,
                env=env,
                cwd=self.exec_info.cwd,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            self.processes[self.hostname] = process
            
            # Start output monitoring threads
            if self.exec_info.collect_output or not self.exec_info.hide_output:
                stdout_thread = threading.Thread(
                    target=self._monitor_output,
                    args=(process.stdout, 'stdout')
                )
                stderr_thread = threading.Thread(
                    target=self._monitor_output,
                    args=(process.stderr, 'stderr')
                )
                
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                
                stdout_thread.start()
                stderr_thread.start()
                
                self.output_threads[self.hostname] = (stdout_thread, stderr_thread)
            
            # Send stdin if provided
            if self.exec_info.stdin:
                try:
                    process.stdin.write(self.exec_info.stdin)
                    process.stdin.close()
                except BrokenPipeError:
                    # Process may have terminated before we could write
                    pass
                    
        except Exception as e:
            print(f"Error starting process: {e}")
            self.exit_code[self.hostname] = 1
            
    def _monitor_output(self, pipe, output_type: str):
        """
        Monitor stdout or stderr in a separate thread.
        
        :param pipe: The pipe to monitor
        :param output_type: 'stdout' or 'stderr'
        """
        output_buffer = []
        
        try:
            for line in iter(pipe.readline, ''):
                if not line:
                    break
                    
                # Store in buffer if collecting output
                if self.exec_info.collect_output:
                    output_buffer.append(line)
                    
                # Print to console if not hidden
                if not self.exec_info.hide_output:
                    if output_type == 'stdout':
                        print(line, end='')
                    else:
                        print(line, end='', file=subprocess.sys.stderr)
                        
                # Write to file if specified
                pipe_file = (self.exec_info.pipe_stdout if output_type == 'stdout' 
                           else self.exec_info.pipe_stderr)
                if pipe_file:
                    try:
                        with open(pipe_file, 'a') as f:
                            f.write(line)
                    except Exception as e:
                        print(f"Error writing to {pipe_file}: {e}")
                        
        except Exception as e:
            print(f"Error monitoring {output_type}: {e}")
        finally:
            pipe.close()
            
        # Store collected output
        if self.exec_info.collect_output:
            if output_type == 'stdout':
                self.stdout[self.hostname] = ''.join(output_buffer)
            else:
                self.stderr[self.hostname] = ''.join(output_buffer)
                
    def wait(self, hostname: str = 'localhost') -> int:
        """Wait for completion and handle sleep"""
        exit_code = super().wait(hostname)
        
        # Sleep if specified
        if self.exec_info.sleep_ms > 0:
            time.sleep(self.exec_info.sleep_ms / 1000.0)
            
        return exit_code


class MpiVersion(LocalExec):
    """
    Introspect the current MPI implementation from the machine using
    mpiexec --version
    """

    def __init__(self, exec_info: ExecInfo):
        self.cmd = 'mpiexec --version'
        
        # Create modified exec_info for introspection
        introspect_info = exec_info.mod(
            env=exec_info.basic_env,
            collect_output=True,
            hide_output=True,
            do_dbg=False
        )
        
        super().__init__(self.cmd, introspect_info)
        
        # Determine MPI version from output
        vinfo = self.stdout.get('localhost', '')
        
        if 'mpich' in vinfo.lower():
            self.version = ExecType.MPICH
        elif 'Open MPI' in vinfo or 'OpenRTE' in vinfo:
            self.version = ExecType.OPENMPI
        elif 'Intel(R) MPI Library' in vinfo:
            self.version = ExecType.INTEL_MPI
        elif 'mpiexec version' in vinfo:
            self.version = ExecType.CRAY_MPICH
        else:
            # Default to MPICH if we can't determine
            print(f"Warning: Could not identify MPI implementation from: {vinfo}")
            self.version = ExecType.MPICH