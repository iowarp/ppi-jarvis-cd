## Application launching

We need to build classes for launching applications. We call these 
executables. Put this in jarvis_cd.shell.

### CoreExec

Every executable should have an exit code and the standard output.
```python
class CoreExec(ABC):
    """
    An abstract class representing a class which is intended to run
    shell commands. This includes SSH, MPI, etc.
    """

    def __init__(self):
        self.exit_code = {} # hostname -> exit_code
        self.stdout = {}  # hostname -> stderr 
        self.stderr = {}  # hostname -> stdout

    @abstractmethod
    def run():
        pass

    @abstractmethod
    def get_cmd():
        pass
```

This is the base class of all future executables.

### ExecInfo

The ExecInfo is a data structure that contains all parameters needed by any
of the executables. Each Exec* class should have a custom ExecInfo. 

For example:
```python
class SshExecInfo(ExecInfo):
  def __init__(self, **kwargs):
    super().__init__(exec_type=ExecType.SSH, **kwargs)
```

At a minimum:
```python
class ExecInfo:
    """
    Contains all information needed to execute a program. This includes
    parameters such as the path to key-pairs, the hosts to run the program
    on, number of processes, etc.
    """
    def __init__(self,  exec_type=ExecType.LOCAL, nprocs=None, ppn=None,
                 user=None, pkey=None, port=None,
                 hostfile=None, env=None,
                 sleep_ms=0, sudo=False, sudoenv=True, cwd=None,
                 collect_output=None, pipe_stdout=None, pipe_stderr=None,
                 hide_output=None, exec_async=False, stdin=None,
                 strict_ssh=False, timeout=None):
        """

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
        """
```

### LocalExec

Takes as input a command and an exec_info data structure.

Main features:
1. Launches a subprocess using the command. The command should just be a direct shell command. Safety is not required. It should launch the process as asynchronous and implement a wait function to wait for completion. If the exec_async parameter of exec_info is False, then wait immediately after launching. Must pass the environment stored in exec_info.
2. Must support the ability to print to console, to a file, and to a string buffer while application is running. It should not collect the stdout buffer all the way at the end of the program. We want to show progress as programs run. This will likely require the use of a thread that polls the output buffer.
3. Must store the return code of the executable.

### SshExec

Inherits from LocalExec.

Takes as input a command and exec_info. Assume passwordless authentication. SshExecInfo can speicfy a public key for connection.
The command should be 

It should route the environment variables in the ssh command as well. 

### PsshExec

Inherits from CoreExec. Should asynchronously launch SshExec commands. One for each item in the hostfile specified in the exec_info.

It will copy the outputs from each individual SshExec and update stdout, stderr, and exit_code

### ScpExec

Takes as input a list of path strings. The paths can be files or directories. They may also contain simple regexes, like /mnt/home/*.txt to copy only certain file types.
Assume the file is located on this host and is being propogated to the remote host. We will never download from the remote host.

It is possible that ScpExec is called with this host. So it may copy a file to the same file that already exists. We need to ensure that the algorithm does not override
the file and make it empty.

Something like this:
```python
class _Scp(LocalExec):
    """
    This class provides methods to copy data over SSH using the "rsync"
    command utility in Linux
    """

    def __init__(self, src_path, dst_path, exec_info):
        """
        Copy a file or directory from source to destination via rsync

        :param src_path: The path to the file on the host
        :param dst_path: The desired file path on the remote host
        :param exec_info: Info needed to execute command with SSH
        """

        self.addr = exec_info.hostfile.hosts[0]
        if self.addr == 'localhost' or self.addr == '127.0.0.1':
            return
        self.src_path = src_path
        self.dst_path = dst_path
        self.user = exec_info.user
        self.pkey = exec_info.pkey
        self.port = exec_info.port
        self.sudo = exec_info.sudo
        self.jutil = JutilManager.get_instance()
        super().__init__(self.rsync_cmd(src_path, dst_path),
                         exec_info.mod(env=exec_info.basic_env))

    def rsync_cmd(self, src_path, dst_path):
        lines = ['rsync -ha']
        if self.pkey is not None or self.port is not None:
            ssh_lines = ['ssh']
            if self.pkey is not None:
                ssh_lines.append(f'-i {self.pkey}')
            if self.port is not None:
                ssh_lines.append(f'-p {self.port}')
            ssh_cmd = ' '.join(ssh_lines)
            lines.append(f'-e \'{ssh_cmd}\'')
        lines.append(src_path)
        if self.user is not None:
            lines.append(f'{self.user}@{self.addr}:{dst_path}')
        else:
            lines.append(f'{self.addr}:{dst_path}')
        rsync_cmd = ' '.join(lines)
        if self.jutil.debug_scp:
            print(rsync_cmd)
        return rsync_cmd


class Scp(Executable):
    """
    Secure copy data between two hosts.
    """

    def __init__(self, paths, exec_info):
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
        if isinstance(paths, str):
            self._exec_single_path(paths)
        if isinstance(paths, list):
            if len(paths) == 0:
                raise Exception('Must have at least one path to scp')
            elif isinstance(paths[0], str):
                self._exec_many_paths(paths)
            elif isinstance(paths[0], tuple):
                self._exec_many_paths_tuple(paths)
            elif isinstance(paths[0], list):
                self._exec_many_paths_tuple(paths)
        if not self.exec_info.exec_async:
            self.wait()

    def _exec_single_path(self, path):
        self.scp_nodes.append(_Scp(path, path, self.exec_info))

    def _exec_many_paths(self, paths):
        for path in paths:
            self.scp_nodes.append(_Scp(path, path, self.exec_info))

    def _exec_many_paths_tuple(self, path_tlist):
        for src, dst in path_tlist:
            self.scp_nodes.append(_Scp(src, dst, self.exec_info))

    def wait(self):
        self.wait_list(self.scp_nodes)
        self.smash_list_outputs(self.scp_nodes)
        self.set_exit_code()
        return self.exit_code

    def set_exit_code(self):
        self.set_exit_code_list(self.scp_nodes)
```

### PscpExec

Similar to PsshExec, but for Scp. Calls asynchronous ScpExec functions and builds stdout, stderr, and exit_code similarly.

### MpiVersion

Introspect the specific mpi version used in this environment:
```python
class MpiVersion(LocalExec):
    """
    Introspect the current MPI implementation from the machine using
    mpirun --version
    """

    def __init__(self, exec_info):
        self.cmd = 'mpiexec --version'
        super().__init__(self.cmd,
                         exec_info.mod(env=exec_info.basic_env,
                                       collect_output=True,
                                       hide_output=True,
                                       do_dbg=False))
        vinfo = self.stdout
        # print(f'MPI INFO: stdout={vinfo} stderr={self.stderr}')
        if 'mpich' in vinfo.lower():
            self.version = ExecType.MPICH
        elif 'Open MPI' in vinfo or 'OpenRTE' in vinfo:
            self.version = ExecType.OPENMPI
        elif 'Intel(R) MPI Library' in vinfo:
            # NOTE(llogan): similar to MPICH
            self.version = ExecType.INTEL_MPI
        elif 'mpiexec version' in vinfo:
            self.version = ExecType.CRAY_MPICH
        else:
            raise Exception(f'Could not identify MPI implementation: {vinfo}')
```

### LocalMpiExec

Base class used by all other mpi implementations:
```python
class LocalMpiExec(LocalExec):
    def __init__(self, cmd, exec_info):
        self.cmd = cmd
        self.nprocs = exec_info.nprocs
        self.ppn = exec_info.ppn
        self.hostfile = exec_info.hostfile
        self.mpi_env = exec_info.env
        if exec_info.do_dbg:
            self.base_cmd = cmd # To append to the extra processes
            self.cmd = self.get_dbg_cmd(cmd, exec_info)
        super().__init__(self.mpicmd(),
                         exec_info.mod(env=exec_info.basic_env,
                                       do_dbg=False))

    @abstractmethod
    def mpicmd(self):
        pass
```

### OpenmpiExec

```python
class OpenMpiExec(LocalMpiExec):
    """
    This class contains methods for executing a command in parallel
    using MPI.
    """
    def mpicmd(self):
        params = [f'mpiexec']
        params.append('--oversubscribe')
        params.append('--allow-run-as-root')  # For docker
        if self.ppn is not None:
            params.append(f'-npernode {self.ppn}')
        if len(self.hostfile):
            if self.hostfile.path is None:
                params.append(f'--host {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')
        params += [f'-x {key}=\"{val}\"'
                   for key, val in self.mpi_env.items()]
        if self.cmd.startswith('gdbserver'):
            params.append(f'-n 1 {self.cmd}')
            if self.nprocs > 1:
                params.append(f': -n {self.nprocs - 1} {self.base_cmd}')
        else:
            params.append(f'-n {self.nprocs}')
            params.append(self.cmd)
        cmd = ' '.join(params)
        return cmd
```

### MpichExec

```python
class MpichExec(LocalMpiExec):
    """
    This class contains methods for executing a command in parallel
    using MPI.
    """

    def mpicmd(self):
        params = ['mpiexec']

        if self.ppn is not None:
            params.append(f'-ppn {self.ppn}')

        if len(self.hostfile):
            if self.hostfile.path is None:
                params.append(f'--host {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')

        params += [f'-genv {key}=\"{val}\"'
                   for key, val in self.mpi_env.items()]

        if self.cmd.startswith('gdbserver'):
            params.append(f'-n 1 {self.cmd}')
            if self.nprocs > 1:
                params.append(f': -n {self.nprocs - 1} {self.base_cmd}')
        else:
            params.append(f'-n {self.nprocs}')
            params.append(self.cmd)

        cmd = ' '.join(params)
        return cmd
```

### CrayMpichExec

```python
class CrayMpichExec(LocalMpiExec):
    """
    This class contains methods for executing a command in parallel
    using MPI.
    """
    def mpicmd(self):
        params = [f'mpiexec -n {self.nprocs}']
        if self.ppn is not None:
            params.append(f'--ppn {self.ppn}')
        if len(self.hostfile):
            if self.hostfile.hosts[0] == 'localhost' and len(self.hostfile) == 1:
                pass
            elif self.hostfile.path is None:
                params.append(f'--hosts {",".join(self.hostfile.hosts)}')
            else:
                params.append(f'--hostfile {self.hostfile.path}')
        params += [f'--env {key}=\"{val}\"'
                   for key, val in self.mpi_env.items()]
        params.append(self.cmd)
        cmd = ' '.join(params) 
        return cmd
```

### Exec

A factory that can be used to call any of the other executables.

## Specific Applications

Add the following to jarvis_cd.shell as system.py

### Kill

Inherits from Exec. Wraps around pkill on Linux.

```
class Kill(Exec):
    """
    Kill all processes which match the name regex.
    """

    def __init__(self, cmd, exec_info, partial=True):
        """
        Kill all processes which match the name regex.

        :param cmd: A regex for the command to kill
        :param exec_info: Info needed to execute the command
        """
        partial_cmd = "-f" if partial else ""
        super().__init__(f"pkill -9 {partial_cmd} {cmd}", exec_info)
```

### GdbServer

Implement a GdbServer Exec class in shell. It inherits from Exec. 

It will take as input a command and a port number. 
It will launch a gdbserver with the command and port.

