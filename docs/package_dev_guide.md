# Jarvis-CD Package Development Guide

This guide explains how to develop custom packages for Jarvis-CD, including the repository structure, abstract methods, and implementation examples.

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [Package Types](#package-types)
3. [Abstract Methods](#abstract-methods)
4. [Environment Variables](#environment-variables)
5. [Configuration](#configuration)
6. [Execution System](#execution-system)
7. [Implementation Examples](#implementation-examples)
8. [Best Practices](#best-practices)

## Repository Structure

Jarvis-CD packages are organized in repositories with the following structure:

```
my_repo/
├── package1/
│   ├── __init__.py
│   └── pkg.py          # Main package implementation
├── package2/
│   ├── __init__.py
│   └── pkg.py
└── __init__.py
```

### Key Requirements

1. **Repository Root**: Contains subdirectories for each package
2. **Package Directory**: Named after the package (e.g., `ior`, `redis`)
3. **Main File**: Must be named `pkg.py` (not `package.py`)
4. **Class Name**: Must be the capitalized package name (e.g., `Ior`, `Redis`)
5. **Init Files**: Include `__init__.py` files for proper Python module structure

### Adding Repositories

```bash
# Add a repository to Jarvis
jarvis repo add /path/to/my_repo

# List registered repositories
jarvis repo list
```

## Package Types

Jarvis-CD provides three base classes for different types of packages:

### 1. Application (jarvis_cd.basic.pkg.Application)

For applications that run and complete automatically (e.g., benchmarks, data processing tools).

```python
from jarvis_cd.basic.pkg import Application

class MyApp(Application):
    def start(self):
        # Run the application
        pass
    
    def stop(self):
        # Usually not needed for applications
        pass
```

### 2. Service (jarvis_cd.basic.pkg.Service)

For long-running services that need manual stopping (e.g., databases, web servers).

```python
from jarvis_cd.basic.pkg import Service

class MyService(Service):
    def start(self):
        # Start the service
        pass
    
    def stop(self):
        # Stop the service
        pass
    
    def status(self) -> str:
        # Return service status
        return "running"
```

### 3. Interceptor (jarvis_cd.basic.pkg.Interceptor)

For packages that modify environment variables to intercept system calls (e.g., profiling tools, I/O interceptors).

```python
from jarvis_cd.basic.pkg import Interceptor

class MyInterceptor(Interceptor):
    def modify_env(self):
        # Modify environment variables
        self.setenv('LD_PRELOAD', '/path/to/my/library.so')
    
    def start(self):
        # Automatically calls modify_env()
        super().start()
```

## Abstract Methods

All packages inherit from the base `Pkg` class and can override these methods:

### Required Override Methods

#### `_init(self)`
**Purpose**: Initialize package-specific variables  
**Called**: During package instantiation  
**Notes**: Don't assume `self.config` is initialized

```python
def _init(self):
    """Initialize package-specific variables"""
    self.my_variable = None
    self.start_time = None
```

#### `_configure_menu(self) -> List[Dict[str, Any]]`
**Purpose**: Define configuration options for the package  
**Called**: When generating CLI help or configuration forms  
**Returns**: List of configuration parameter dictionaries

```python
def _configure_menu(self):
    """Define configuration options"""
    return [
        {
            'name': 'param_name',
            'msg': 'Description of parameter',
            'type': str,
            'default': 'default_value',
            'choices': ['option1', 'option2'],  # Optional
            'aliases': ['alias1', 'alias2'],    # Optional
        }
    ]
```

### Lifecycle Methods

#### `configure(self, **kwargs)`
**Purpose**: Handle package configuration  
**Called**: When package is configured via CLI or programmatically  
**Use**: Set up environment variables with `self.env` and `self.mod_env`

```python
def configure(self, **kwargs):
    """Configure the package"""
    self.update_config(kwargs, rebuild=False)
    
    # Set environment variables
    if self.config['custom_path']:
        self.setenv('MY_APP_PATH', self.config['custom_path'])
        self.prepend_env('PATH', self.config['custom_path'] + '/bin')
```

#### `start(self)`
**Purpose**: Start the package (application, service, or interceptor)  
**Called**: During `jarvis ppl run` and `jarvis ppl start`

```python
def start(self):
    """Start the package"""
    # Use self.mod_env for environment variables
    # Use self.jarvis.hostfile for MPI execution
    cmd = ['my_application', '--config', self.config['config_file']]
    Exec(' '.join(cmd), LocalExecInfo(env=self.mod_env)).run()
```

#### `stop(self)`
**Purpose**: Stop the package  
**Called**: During `jarvis ppl run` and `jarvis ppl stop`

```python
def stop(self):
    """Stop the package"""
    # Gracefully shutdown the application/service
    pass
```

#### `kill(self)`
**Purpose**: Forcibly terminate the package  
**Called**: During `jarvis ppl kill`

```python
def kill(self):
    """Forcibly kill the package"""
    from jarvis_cd.shell.process import Kill
    Kill('my_application', PsshExecInfo(hostfile=self.jarvis.hostfile)).run()
```

#### `clean(self)`
**Purpose**: Clean up package data and temporary files  
**Called**: During `jarvis ppl clean`

```python
def clean(self):
    """Clean package data"""
    from jarvis_cd.shell.process import Rm
    Rm(self.config['output_dir'], 
       PsshExecInfo(hostfile=self.jarvis.hostfile)).run()
```

#### `status(self) -> str`
**Purpose**: Return current package status  
**Called**: During `jarvis ppl status`

```python
def status(self) -> str:
    """Return package status"""
    # Check if process is running, files exist, etc.
    return "running" | "stopped" | "error" | "unknown"
```

## Environment Variables

Jarvis-CD manages environment variables through a pipeline-wide system where environment modifications are propagated between packages.

### Environment Loading

When a pipeline is first loaded, the environment is constructed from:
1. **Pipeline Configuration** (`pipeline.yaml` - `env` section)
2. **Environment File** (`env.yaml` in pipeline directory)  
3. **System Environment** (current shell environment)

### Package Environment Dictionaries

Each package has two environment dictionaries:

### `self.env`
- **Purpose**: Shared environment across the pipeline
- **Source**: Loaded from pipeline environment + modifications from previous packages
- **Propagation**: Changes are propagated to subsequent packages in the pipeline
- **Usage**: Use this to set environment variables that should affect later packages

### `self.mod_env`
- **Purpose**: Package-specific environment copy
- **Source**: Deep copy of `self.env` at package load time
- **Scope**: Private to the package, not propagated
- **Usage**: Used in execution commands, modified by interceptors

### Environment Methods

```python
# Set an environment variable
self.setenv('MY_VAR', 'value')

# Prepend to PATH-like variables
self.prepend_env('PATH', '/new/path')
self.prepend_env('LD_LIBRARY_PATH', '/new/lib')

# Track existing environment variables
self.track_env({'EXISTING_VAR': os.environ.get('EXISTING_VAR', '')})
```

### Environment Propagation

Environment changes are automatically propagated between packages:

```python
# Package 1 (e.g., compiler setup)
def configure(self, **kwargs):
    self.setenv('CC', '/usr/bin/gcc-9')
    self.prepend_env('PATH', '/opt/compiler/bin')

# Package 2 (automatically receives Package 1's environment)
def start(self):
    # self.env now contains CC and PATH from Package 1
    # self.mod_env is a deep copy for this package's use
    Exec('make', LocalExecInfo(env=self.mod_env)).run()
```

### Usage in configure()

**Always use environment methods in the `configure()` method:**

```python
def configure(self, **kwargs):
    """Configure package and set environment"""
    self.update_config(kwargs, rebuild=False)
    
    # Set application-specific environment (will be propagated to later packages)
    if self.config['install_path']:
        self.setenv('MY_APP_HOME', self.config['install_path'])
        self.prepend_env('PATH', f"{self.config['install_path']}/bin")
        self.prepend_env('LD_LIBRARY_PATH', f"{self.config['install_path']}/lib")
    
    # Track system environment if needed
    if 'CUDA_HOME' in os.environ:
        self.track_env({'CUDA_HOME': os.environ['CUDA_HOME']})
```

## Configuration

### Configuration Parameters

Each parameter in `_configure_menu()` supports these fields:

- **`name`** (required): Parameter name
- **`msg`** (required): Description for help text
- **`type`** (required): `str`, `int`, `float`, `bool`
- **`default`**: Default value
- **`choices`**: List of valid options
- **`aliases`**: Alternative parameter names
- **`required`**: Whether parameter is mandatory

### Configuration Access

```python
# Access configuration values
def start(self):
    input_file = self.config['input_file']
    num_procs = self.config['nprocs']
    debug_mode = self.config['debug']
```

## Execution System

### Available Execution Classes

```python
from jarvis_cd.shell import Exec, LocalExecInfo, MpiExecInfo, PsshExecInfo, SshExecInfo
from jarvis_cd.shell.process import Kill, Rm, Mkdir, Chmod, Which

# Local execution
Exec('command', LocalExecInfo(env=self.mod_env)).run()

# MPI execution
Exec('mpi_command', MpiExecInfo(
    env=self.mod_env,
    hostfile=self.jarvis.hostfile,
    nprocs=self.config['nprocs'],
    ppn=self.config['ppn']
)).run()

# Parallel SSH execution
Exec('command', PsshExecInfo(
    env=self.mod_env,
    hostfile=self.jarvis.hostfile
)).run()

# Process utilities
Kill('process_name', PsshExecInfo(hostfile=self.jarvis.hostfile)).run()
Rm('/path/to/clean', LocalExecInfo()).run()
```

### Hostfile Access

```python
# Access the hostfile for distributed execution
hostfile = self.jarvis.hostfile

# Use in MPI commands
exec_info = MpiExecInfo(
    hostfile=hostfile,
    nprocs=len(hostfile),  # Number of hosts
    ppn=4  # Processes per node
)
```

## Implementation Examples

### Simple Application Example

```python
"""
Simple benchmark application package.
"""
from jarvis_cd.basic.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo
import os

class SimpleBench(Application):
    """Simple benchmark application"""
    
    def _init(self):
        """Initialize variables"""
        self.output_file = None
    
    def _configure_menu(self):
        """Configuration options"""
        return [
            {
                'name': 'duration',
                'msg': 'Benchmark duration in seconds',
                'type': int,
                'default': 60
            },
            {
                'name': 'output_dir',
                'msg': 'Output directory for results',
                'type': str,
                'default': '/tmp/benchmark'
            }
        ]
    
    def configure(self, **kwargs):
        """Configure the benchmark"""
        self.update_config(kwargs, rebuild=False)
        
        # Set up output directory
        os.makedirs(self.config['output_dir'], exist_ok=True)
        self.output_file = os.path.join(self.config['output_dir'], 'results.txt')
        
        # Set environment variables
        self.setenv('BENCH_OUTPUT_DIR', self.config['output_dir'])
    
    def start(self):
        """Run the benchmark"""
        cmd = [
            'benchmark_tool',
            '--duration', str(self.config['duration']),
            '--output', self.output_file
        ]
        
        Exec(' '.join(cmd), LocalExecInfo(env=self.mod_env)).run()
    
    def clean(self):
        """Clean benchmark output"""
        if self.output_file and os.path.exists(self.output_file):
            os.remove(self.output_file)
```

### MPI Application Example

```python
"""
MPI-based parallel application package.
"""
from jarvis_cd.basic.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo, MpiExecInfo
from jarvis_cd.shell.process import Rm
import os

class ParallelApp(Application):
    """Parallel MPI application"""
    
    def _configure_menu(self):
        """Configuration options"""
        return [
            {
                'name': 'nprocs',
                'msg': 'Number of MPI processes',
                'type': int,
                'default': 4
            },
            {
                'name': 'ppn',
                'msg': 'Processes per node',
                'type': int,
                'default': 2
            },
            {
                'name': 'input_file',
                'msg': 'Input data file',
                'type': str,
                'default': 'input.dat'
            }
        ]
    
    def configure(self, **kwargs):
        """Configure the application"""
        self.update_config(kwargs, rebuild=False)
        
        # Set MPI environment
        self.setenv('PARALLEL_APP_INPUT', self.config['input_file'])
    
    def start(self):
        """Run parallel application"""
        # Check for MPI executable
        Exec('which mpiexec', LocalExecInfo(env=self.mod_env)).run()
        
        # Run MPI application
        cmd = ['parallel_app', '--input', self.config['input_file']]
        
        Exec(' '.join(cmd), MpiExecInfo(
            env=self.mod_env,
            hostfile=self.jarvis.hostfile,
            nprocs=self.config['nprocs'],
            ppn=self.config['ppn']
        )).run()
    
    def clean(self):
        """Clean output files"""
        Rm('output_*', LocalExecInfo()).run()
```

### Service Example

```python
"""
Database service package.
"""
from jarvis_cd.basic.pkg import Service
from jarvis_cd.shell import Exec, LocalExecInfo
from jarvis_cd.shell.process import Kill, Which
import os
import time

class Database(Service):
    """Database service"""
    
    def _init(self):
        """Initialize service variables"""
        self.pid_file = None
        self.data_dir = None
    
    def _configure_menu(self):
        """Configuration options"""
        return [
            {
                'name': 'port',
                'msg': 'Database port',
                'type': int,
                'default': 5432
            },
            {
                'name': 'data_dir',
                'msg': 'Database data directory',
                'type': str,
                'default': '/var/lib/mydb'
            }
        ]
    
    def configure(self, **kwargs):
        """Configure database"""
        self.update_config(kwargs, rebuild=False)
        
        self.data_dir = self.config['data_dir']
        self.pid_file = os.path.join(self.data_dir, 'mydb.pid')
        
        # Set database environment
        self.setenv('MYDB_PORT', str(self.config['port']))
        self.setenv('MYDB_DATA_DIR', self.data_dir)
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
    
    def start(self):
        """Start database service"""
        # Check if database is available
        Which('mydb_server', LocalExecInfo()).run()
        
        # Start database
        cmd = [
            'mydb_server',
            '--port', str(self.config['port']),
            '--data-dir', self.data_dir,
            '--pid-file', self.pid_file,
            '--daemonize'
        ]
        
        Exec(' '.join(cmd), LocalExecInfo(env=self.mod_env)).run()
        
        # Wait for service to start
        time.sleep(2)
    
    def stop(self):
        """Stop database service"""
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                pid = f.read().strip()
            
            Exec(f'kill {pid}', LocalExecInfo()).run()
    
    def kill(self):
        """Force kill database"""
        Kill('mydb_server', LocalExecInfo()).run()
    
    def status(self) -> str:
        """Check database status"""
        if os.path.exists(self.pid_file):
            return "running"
        return "stopped"
    
    def clean(self):
        """Clean database data"""
        Rm(self.data_dir, LocalExecInfo()).run()
```

### Interceptor Example

```python
"""
Performance profiling interceptor package.
"""
from jarvis_cd.basic.pkg import Interceptor
import os

class Profiler(Interceptor):
    """Performance profiling interceptor"""
    
    def _init(self):
        """Initialize profiler variables"""
        self.profiler_lib = None
    
    def _configure_menu(self):
        """Configuration options"""
        return [
            {
                'name': 'profiler_path',
                'msg': 'Path to profiler library',
                'type': str,
                'default': '/usr/lib/libprofiler.so'
            },
            {
                'name': 'output_file',
                'msg': 'Profiler output file',
                'type': str,
                'default': 'profile_output.txt'
            }
        ]
    
    def configure(self, **kwargs):
        """Configure profiler"""
        self.update_config(kwargs, rebuild=False)
        
        self.profiler_lib = self.config['profiler_path']
        
        # Set profiler environment
        self.setenv('PROFILER_OUTPUT', self.config['output_file'])
    
    def modify_env(self):
        """Set up profiling environment"""
        # Add profiler library to LD_PRELOAD
        if os.path.exists(self.profiler_lib):
            current_preload = self.mod_env.get('LD_PRELOAD', '')
            if current_preload:
                self.setenv('LD_PRELOAD', f"{self.profiler_lib}:{current_preload}")
            else:
                self.setenv('LD_PRELOAD', self.profiler_lib)
    
    def clean(self):
        """Clean profiler output"""
        output_file = self.config['output_file']
        if os.path.exists(output_file):
            os.remove(output_file)
```

## Best Practices

### 1. Use Environment Variables Correctly

```python
# ✅ Good - Use in configure()
def configure(self, **kwargs):
    self.update_config(kwargs, rebuild=False)
    self.setenv('MY_APP_HOME', self.config['install_path'])

# ✅ Good - Use mod_env in execution
def start(self):
    Exec('command', LocalExecInfo(env=self.mod_env)).run()

# ❌ Bad - Don't set environment in start()
def start(self):
    self.setenv('LATE_VAR', 'value')  # Too late!
```

### 2. Handle File Paths Properly

```python
def configure(self, **kwargs):
    self.update_config(kwargs, rebuild=False)
    
    # Expand environment variables in paths
    output_dir = os.path.expandvars(self.config['output_dir'])
    
    # Create directories as needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Store absolute paths
    self.output_dir = os.path.abspath(output_dir)
```

### 3. Use Proper Execution Commands

```python
def start(self):
    # ✅ Good - Use .run() method
    Exec('command', LocalExecInfo(env=self.mod_env)).run()
    
    # ✅ Good - Use process utilities
    from jarvis_cd.shell.process import Mkdir
    Mkdir('/path/to/dir', LocalExecInfo()).run()
    
    # ❌ Bad - Don't use subprocess directly
    import subprocess
    subprocess.run(['command'])  # Don't do this
```

### 4. Implement Proper Cleanup

```python
def clean(self):
    """Clean all package data"""
    # Remove output files
    if hasattr(self, 'output_dir') and os.path.exists(self.output_dir):
        Rm(self.output_dir, LocalExecInfo()).run()
    
    # Remove temporary files
    Rm('/tmp/myapp_*', LocalExecInfo()).run()
```

### 5. Error Handling

```python
def start(self):
    """Start with error handling"""
    try:
        # Check prerequisites
        Which('required_command', LocalExecInfo()).run()
        
        # Run main command
        result = Exec('main_command', LocalExecInfo(env=self.mod_env)).run()
        
        # Check result if needed
        if hasattr(result, 'exit_code') and result.exit_code != 0:
            raise RuntimeError("Command failed")
            
    except Exception as e:
        print(f"Error starting {self.__class__.__name__}: {e}")
        raise
```

### 6. Documentation

```python
class MyPackage(Application):
    """
    Brief description of what this package does.
    
    This package provides functionality for...
    """
    
    def _configure_menu(self):
        """
        Define configuration parameters.
        
        For more details on parameter format, see:
        https://docs.jarvis-cd.io/configuration
        """
        return [
            {
                'name': 'param',
                'msg': 'Clear description of parameter purpose',
                'type': str,
                'default': 'sensible_default'
            }
        ]
```

This guide provides the foundation for developing robust Jarvis-CD packages. For more advanced topics, refer to the existing builtin packages in the `builtin/` directory for real-world examples.