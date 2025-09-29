# Jarvis-CD Shell Execution System

This guide documents the shell execution system in `jarvis_cd.shell`, which provides comprehensive command execution capabilities for local, remote, and parallel execution.

## Table of Contents

1. [Overview](#overview)
2. [Execution Types](#execution-types)
3. [Factory Pattern](#factory-pattern)
4. [Core Classes](#core-classes)
5. [Process Utilities](#process-utilities)
6. [Usage Examples](#usage-examples)
7. [Best Practices](#best-practices)

## Overview

The Jarvis-CD shell system provides a unified interface for executing commands across different environments:

- **Local execution**: Commands run on the local machine
- **SSH execution**: Commands run on remote hosts via SSH
- **MPI execution**: Parallel commands using MPI frameworks
- **File transfer**: Secure copying between hosts
- **Process utilities**: Common system operations

All execution classes follow a consistent interface and provide proper error handling, output collection, and process management.

## Execution Types

### ExecType Enumeration

```python
from jarvis_cd.shell import ExecType

# Available execution types
ExecType.LOCAL      # Local execution
ExecType.SSH        # Single SSH connection
ExecType.PSSH       # Parallel SSH (multiple hosts)
ExecType.MPI        # MPI with auto-detection
ExecType.OPENMPI    # Specific OpenMPI
ExecType.MPICH      # Specific MPICH
ExecType.INTEL_MPI  # Intel MPI
ExecType.CRAY_MPICH # Cray MPICH
ExecType.SCP        # Secure copy
ExecType.PSCP       # Parallel secure copy
```

### ExecInfo Classes

Each execution type has a corresponding `ExecInfo` class that holds execution parameters:

```python
from jarvis_cd.shell import LocalExecInfo, SshExecInfo, MpiExecInfo

# Local execution info
local_info = LocalExecInfo(
    env={'PATH': '/custom/path'},
    cwd='/working/directory',
    timeout=30
)

# SSH execution info
ssh_info = SshExecInfo(
    hostfile=hostfile,
    user='myuser',
    pkey='/path/to/key',
    port=22
)

# MPI execution info
mpi_info = MpiExecInfo(
    hostfile=hostfile,
    nprocs=8,
    ppn=2,
    env={'OMP_NUM_THREADS': '4'}
)
```

## Factory Pattern

### Exec Factory Class

The `Exec` class acts as a factory that automatically selects the appropriate executor based on the `ExecInfo` type:

```python
from jarvis_cd.shell import Exec, LocalExecInfo, MpiExecInfo

# Automatically uses LocalExec
result = Exec('ls -la', LocalExecInfo()).run()

# Automatically uses MpiExec
result = Exec('./parallel_app', MpiExecInfo(nprocs=4)).run()
```

## Core Classes

### LocalExec

Execute commands on the local machine using subprocess.

```python
from jarvis_cd.shell import LocalExec, LocalExecInfo

exec_info = LocalExecInfo(
    env={'MYVAR': 'value'},
    cwd='/tmp',
    collect_output=True,
    hide_output=False
)

executor = LocalExec('python script.py', exec_info)
executor.run()

# Access results
print(f"Exit code: {executor.exit_code['localhost']}")
print(f"Output: {executor.stdout['localhost']}")
print(f"Errors: {executor.stderr['localhost']}")
```

### SshExec

Execute commands on a single remote host via SSH.

```python
from jarvis_cd.shell import SshExec, SshExecInfo
from jarvis_cd.util.hostfile import Hostfile

hostfile = Hostfile(['remote.server.com'])
exec_info = SshExecInfo(
    hostfile=hostfile,
    user='username',
    pkey='/path/to/private/key',
    strict_ssh=False
)

executor = SshExec('hostname && uptime', exec_info)
executor.run()

# Results are keyed by hostname
hostname = hostfile.hosts[0]
print(f"Output from {hostname}: {executor.stdout[hostname]}")
```

### PsshExec

Execute commands on multiple hosts in parallel.

```python
from jarvis_cd.shell import PsshExec, PsshExecInfo
from jarvis_cd.util.hostfile import Hostfile

hostfile = Hostfile(['host1.com', 'host2.com', 'host3.com'])
exec_info = PsshExecInfo(
    hostfile=hostfile,
    user='username',
    pkey='/path/to/key'
)

executor = PsshExec('df -h', exec_info)
executor.run()

# Wait for all hosts to complete
results = executor.wait_all()

# Access results per host
for hostname in hostfile.hosts:
    print(f"Host {hostname}:")
    print(f"  Exit code: {executor.exit_code[hostname]}")
    print(f"  Output: {executor.stdout[hostname]}")
```

### MpiExec

Execute MPI applications with automatic MPI implementation detection.

```python
from jarvis_cd.shell import MpiExec, MpiExecInfo
from jarvis_cd.util.hostfile import Hostfile

hostfile = Hostfile(['node1', 'node2', 'node3'])
exec_info = MpiExecInfo(
    hostfile=hostfile,
    nprocs=12,          # Total processes
    ppn=4,              # Processes per node
    env={
        'OMP_NUM_THREADS': '2',
        'MPI_BUFFER_SIZE': '32M'
    }
)

executor = MpiExec('./my_mpi_app input.dat', exec_info)
executor.run()

# MPI output is typically from rank 0
print(f"MPI output: {executor.stdout['localhost']}")
```

### ScpExec and PscpExec

Transfer files between hosts using rsync over SSH.

```python
from jarvis_cd.shell import ScpExec, ScpExecInfo
from jarvis_cd.util.hostfile import Hostfile

hostfile = Hostfile(['remote.host.com'])
exec_info = ScpExecInfo(
    hostfile=hostfile,
    user='username',
    pkey='/path/to/key'
)

# Single file copy
executor = ScpExec('/local/file.txt', exec_info)
executor.run()

# Multiple files with custom destinations
file_pairs = [
    ('/local/config.yml', '/remote/app/config.yml'),
    ('/local/data/', '/remote/app/data/'),
]
executor = ScpExec(file_pairs, exec_info)
executor.run()

# Check transfer results
for hostname in hostfile.hosts:
    if executor.exit_code[hostname] == 0:
        print(f"Transfer to {hostname} successful")
    else:
        print(f"Transfer to {hostname} failed: {executor.stderr[hostname]}")
```

## Process Utilities

### Kill

Terminate processes by name pattern.

```python
from jarvis_cd.shell.process import Kill
from jarvis_cd.shell import LocalExecInfo, PsshExecInfo

# Kill local processes
Kill('python.*my_script', LocalExecInfo()).run()

# Kill processes on remote hosts
Kill('my_application', PsshExecInfo(hostfile=hostfile)).run()

# Exact name matching (partial=False)
Kill('nginx', LocalExecInfo(), partial=False).run()
```

### KillAll

Kill all processes owned by the current user.

```python
from jarvis_cd.shell.process import KillAll
from jarvis_cd.shell import PsshExecInfo

# Kill all user processes on remote hosts
KillAll(PsshExecInfo(hostfile=hostfile)).run()
```

### Which

Find executable locations.

```python
from jarvis_cd.shell.process import Which
from jarvis_cd.shell import LocalExecInfo

which = Which('mpiexec', LocalExecInfo())
which.run()

if which.exists():
    print(f"mpiexec found at: {which.get_path()}")
else:
    print("mpiexec not found in PATH")
```

### Mkdir

Create directories with proper options.

```python
from jarvis_cd.shell.process import Mkdir
from jarvis_cd.shell import LocalExecInfo, PsshExecInfo

# Create local directories
Mkdir(['/tmp/output', '/tmp/logs'], LocalExecInfo()).run()

# Create directories on remote hosts
Mkdir('/shared/data', PsshExecInfo(hostfile=hostfile), parents=True).run()
```

### Rm

Remove files and directories.

```python
from jarvis_cd.shell.process import Rm
from jarvis_cd.shell import LocalExecInfo, PsshExecInfo

# Remove local files
Rm('/tmp/temp_data*', LocalExecInfo(), recursive=True).run()

# Remove files on remote hosts
Rm(['/tmp/log1.txt', '/tmp/log2.txt'], PsshExecInfo(hostfile=hostfile)).run()
```

### Chmod

Change file permissions.

```python
from jarvis_cd.shell.process import Chmod
from jarvis_cd.shell import LocalExecInfo

# Make scripts executable
Chmod('/path/to/script.sh', '+x', LocalExecInfo()).run()

# Set specific permissions recursively
Chmod('/data/directory', '755', LocalExecInfo(), recursive=True).run()
```

### Sleep

Pause execution for a specified duration.

```python
from jarvis_cd.shell.process import Sleep
from jarvis_cd.shell import LocalExecInfo

# Sleep for 5 seconds
Sleep(5, LocalExecInfo()).run()

# Sleep for 1.5 seconds
Sleep(1.5, LocalExecInfo()).run()
```

### Echo

Print text to stdout.

```python
from jarvis_cd.shell.process import Echo
from jarvis_cd.shell import LocalExecInfo

Echo("Processing complete", LocalExecInfo()).run()
```

## Usage Examples

### Basic Package Implementation

```python
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo, MpiExecInfo
from jarvis_cd.shell.process import Which, Mkdir, Rm

class MyBenchmark(Application):
    def configure(self, **kwargs):
        self.update_config(kwargs, rebuild=False)
        
        # Set up environment
        self.setenv('BENCHMARK_HOME', self.config['install_path'])
        self.prepend_env('PATH', f"{self.config['install_path']}/bin")
        
    def start(self):
        # Check prerequisites
        which = Which('benchmark_tool', LocalExecInfo(env=self.mod_env))
        which.run()
        if not which.exists():
            raise RuntimeError("benchmark_tool not found in PATH")
            
        # Create output directory
        Mkdir(self.config['output_dir'], LocalExecInfo()).run()
        
        # Run benchmark
        if self.config.get('use_mpi', False):
            exec_info = MpiExecInfo(
                env=self.mod_env,
                hostfile=self.jarvis.hostfile,
                nprocs=self.config['nprocs'],
                ppn=self.config['ppn']
            )
        else:
            exec_info = LocalExecInfo(env=self.mod_env)
            
        cmd = [
            'benchmark_tool',
            '--input', self.config['input_file'],
            '--output', self.config['output_dir'],
            '--iterations', str(self.config['iterations'])
        ]
        
        Exec(' '.join(cmd), exec_info).run()
        
    def clean(self):
        # Remove output files
        Rm(self.config['output_dir'], LocalExecInfo(), recursive=True).run()
```

### Interceptor Implementation

```python
from jarvis_cd.core.pkg import Interceptor
from jarvis_cd.shell.process import Which

class ProfilingInterceptor(Interceptor):
    def configure(self, **kwargs):
        self.update_config(kwargs, rebuild=False)
        
        # Find profiling library
        profiler_lib = self.find_library('profiler')
        if not profiler_lib:
            raise RuntimeError("Profiling library not found")
            
        self.profiler_path = profiler_lib
        
    def modify_env(self):
        # Add profiler to LD_PRELOAD
        current_preload = self.mod_env.get('LD_PRELOAD', '')
        if current_preload:
            preload_value = f"{self.profiler_path}:{current_preload}"
        else:
            preload_value = self.profiler_path
            
        self.setenv('LD_PRELOAD', preload_value)
        self.setenv('PROFILER_OUTPUT', self.config['output_file'])
```

### Complex Multi-Host Deployment

```python
from jarvis_cd.shell import PsshExec, ScpExec, PsshExecInfo, ScpExecInfo
from jarvis_cd.shell.process import Kill, Mkdir
from jarvis_cd.util.hostfile import Hostfile

def deploy_application(hostfile, config):
    """Deploy application to multiple hosts"""
    
    # Create execution info
    exec_info = PsshExecInfo(
        hostfile=hostfile,
        user=config['user'],
        pkey=config['private_key']
    )
    
    # 1. Stop any existing instances
    Kill('my_application', exec_info).run()
    
    # 2. Create necessary directories
    Mkdir(['/app/data', '/app/logs'], exec_info, parents=True).run()
    
    # 3. Copy application files
    files_to_copy = [
        ('/local/app/binary', '/app/binary'),
        ('/local/app/config/', '/app/config/'),
        ('/local/app/data/', '/app/data/')
    ]
    
    scp_info = ScpExecInfo(
        hostfile=hostfile,
        user=config['user'],
        pkey=config['private_key']
    )
    
    ScpExec(files_to_copy, scp_info).run()
    
    # 4. Set permissions
    Chmod('/app/binary', '+x', exec_info).run()
    
    # 5. Start application
    start_cmd = '/app/binary --config /app/config/app.conf --daemon'
    PsshExec(start_cmd, exec_info).run()
    
    # 6. Verify startup
    Sleep(2).run()
    PsshExec('pgrep -f my_application', exec_info).run()
```

## Best Practices

### 1. CRITICAL: Always Call .run() to Execute Commands

**MOST IMPORTANT**: All Exec objects and process utilities must call `.run()` to actually execute commands. Simply creating an Exec object does not execute anything.

```python
# ✅ Correct - Execute the command
from jarvis_cd.shell import Exec, LocalExecInfo

Exec('ls -la', LocalExecInfo()).run()

# ❌ Wrong - Command is never executed
Exec('ls -la', LocalExecInfo())  # Does nothing!

# ✅ Correct - Store executor and run
executor = Exec('./my_app', LocalExecInfo())
executor.run()

# ✅ Correct - Process utilities also need .run()
from jarvis_cd.shell.process import Mkdir, Rm, Which

Which('required_tool', LocalExecInfo()).run()
Mkdir('/output/dir', LocalExecInfo()).run()
Rm('/tmp/files*', LocalExecInfo()).run()

# ❌ Wrong - These commands are never executed
Which('required_tool', LocalExecInfo())  # Check not performed!
Mkdir('/output/dir', LocalExecInfo())    # Directory not created!
Rm('/tmp/files*', LocalExecInfo())       # Files not removed!
```

This is the most common mistake when using the shell system and will cause commands to appear to work but actually do nothing.

### 2. Always Use ExecInfo Classes

```python
# ✅ Good - Use proper ExecInfo
from jarvis_cd.shell import Exec, LocalExecInfo

Exec('command', LocalExecInfo(env=self.mod_env)).run()

# ❌ Bad - Don't create ExecInfo manually
from jarvis_cd.shell.exec_info import ExecInfo, ExecType

exec_info = ExecInfo(exec_type=ExecType.LOCAL)  # Don't do this
```

### 3. Handle Errors Properly

```python
executor = Exec('risky_command', LocalExecInfo())
executor.run()

# Check exit codes
if executor.exit_code['localhost'] != 0:
    error_msg = executor.stderr['localhost']
    raise RuntimeError(f"Command failed: {error_msg}")
```

### 4. Use Environment Variables Correctly

```python
# ✅ Good - Use package environment
def start(self):
    exec_info = LocalExecInfo(env=self.mod_env)
    Exec('my_command', exec_info).run()

# ❌ Bad - Don't use system environment
def start(self):
    exec_info = LocalExecInfo()  # Uses system env
    Exec('my_command', exec_info).run()
```

### 5. Clean Up Resources

```python
def clean(self):
    # Kill processes
    Kill('my_application', PsshExecInfo(hostfile=self.jarvis.hostfile)).run()
    
    # Remove files
    Rm('/tmp/my_app_*', LocalExecInfo(), recursive=True).run()
    
    # Wait a moment for cleanup
    Sleep(1).run()
```

### 6. Use Process Utilities

```python
# ✅ Good - Use utility classes
from jarvis_cd.shell.process import Which, Mkdir, Rm

Which('required_tool', LocalExecInfo()).run()
Mkdir('/output/dir', LocalExecInfo()).run()

# ❌ Bad - Don't construct commands manually
Exec('which required_tool', LocalExecInfo()).run()
Exec('mkdir -p /output/dir', LocalExecInfo()).run()
```

### 7. Handle Timeouts

```python
# Set reasonable timeouts for long-running commands
exec_info = LocalExecInfo(timeout=300)  # 5 minutes
Exec('long_running_command', exec_info).run()
```

### 8. Use Proper File Transfer

```python
# ✅ Good - Use ScpExec for file transfers
from jarvis_cd.shell import ScpExec, ScpExecInfo

ScpExec('/local/file', ScpExecInfo(hostfile=hostfile)).run()

# ❌ Bad - Don't use SSH for file copying
from jarvis_cd.shell import SshExec

SshExec('cp /local/file /remote/file', ssh_info).run()  # Won't work
```

The Jarvis-CD shell system provides a robust foundation for command execution across diverse computing environments. By following these patterns and best practices, you can create reliable, maintainable packages that work consistently across different deployment scenarios.