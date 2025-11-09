# Jarvis-CD Pipeline Documentation

This comprehensive guide covers pipeline management, YAML configuration, filesystem organization, and CLI commands in Jarvis-CD.

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [Pipeline Filesystem Structure](#pipeline-filesystem-structure)
3. [Pipeline YAML Format](#pipeline-yaml-format)
4. [Pipeline CLI Commands](#pipeline-cli-commands)
5. [Pipeline Lifecycle](#pipeline-lifecycle)
6. [Environment Management](#environment-management)
7. [Pipeline Indexes](#pipeline-indexes)
8. [Advanced Pipeline Features](#advanced-pipeline-features)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Pipeline Overview

A **pipeline** in Jarvis-CD is a coordinated sequence of packages (applications, services, and interceptors) that execute together to accomplish a specific computational task. Pipelines provide:

- **Package Coordination**: Sequential or parallel execution of multiple packages
- **Environment Propagation**: Shared environment variables across package executions
- **Interceptor Integration**: Runtime environment modification for profiling, debugging, and monitoring
- **Configuration Management**: Centralized configuration for all pipeline components
- **State Management**: Persistent pipeline state and package configurations

### Key Concepts

- **Package**: Individual computational unit (application, service, or interceptor)
- **Interceptor**: Environment modifier that affects package execution (profiling, I/O tracing, etc.)
- **Environment**: Shared environment variables propagated between packages
- **Configuration**: Package-specific parameters and settings
- **Global ID**: Unique identifier in format `pipeline_name.package_id`

## Pipeline Filesystem Structure

Pipelines are organized in a hierarchical filesystem structure that provides isolation, persistence, and organization.

### User Configuration Directory Structure

```
~/.ppi-jarvis/
├── config/
│   ├── jarvis.yaml              # Global Jarvis configuration
│   ├── packages/                # Standalone package configurations
│   └── pipelines/               # Pipeline storage directory
│       ├── pipeline1/           # Individual pipeline directory
│       │   ├── pipeline.yaml    # Pipeline configuration
│       │   ├── env.yaml        # Environment variables
│       │   └── packages/       # Package-specific directories
│       │       ├── pkg1/       # Package instance directory
│       │       │   ├── config/ # Package configuration files
│       │       │   ├── shared/ # Shared runtime files
│       │       │   └── private/# Private package data
│       │       └── pkg2/
│       └── pipeline2/
├── shared/                     # Global shared data directory
└── private/                    # Global private data directory
```

### Pipeline Directory Structure

Each pipeline gets its own isolated directory:

```
~/.ppi-jarvis/config/pipelines/my_pipeline/
├── pipeline.yaml              # Main pipeline configuration
├── env.yaml                   # Pipeline environment variables
└── packages/                  # Package instance storage
    ├── app1/                  # Package instance directory
    │   ├── config/           # Generated configuration files
    │   │   ├── config.yaml   # Package configuration
    │   │   ├── env.yaml      # Package environment
    │   │   └── mod_env.yaml  # Modified environment (with LD_PRELOAD)
    │   ├── shared/           # Shared files accessible to other packages
    │   └── private/          # Private package data
    ├── database/
    │   ├── config/
    │   ├── shared/
    │   └── private/
    └── profiler/             # Interceptor instance directory
        ├── config/
        ├── shared/
        └── private/
```

### Directory Purposes

#### Pipeline Level
- **`pipeline.yaml`**: Main configuration including packages, interceptors, and metadata
- **`env.yaml`**: Environment variables shared across all packages in the pipeline

#### Package Level  
- **`config/`**: Package-specific configuration files and generated configs
- **`shared/`**: Files that can be accessed by other packages in the pipeline
- **`private/`**: Package-specific private data not shared with other packages

### File Lifecycle

1. **Pipeline Creation**: `pipeline.yaml` and `env.yaml` created
2. **Package Addition**: Package directory structure created under `packages/`
3. **Configuration**: Package `config/` populated with configuration files
4. **Execution**: Runtime files generated in `shared/` and `private/`
5. **Cleanup**: Package directories can be cleaned while preserving configuration

## Pipeline YAML Format

Pipeline YAML files define the complete pipeline configuration including packages, interceptors, environment, and metadata.

### Basic Pipeline Structure

```yaml
# Pipeline name (required)
name: my_pipeline

# Environment configuration (optional)
# Must be a named environment reference or omitted
env: my_custom_environment  # References a named environment

# Main packages (required)
pkgs:
  - pkg_type: repo.package_name
    pkg_name: instance_name
    # Package configuration parameters
    param1: value1
    param2: value2

# Interceptors (optional)
interceptors:
  - pkg_type: repo.interceptor_name
    pkg_name: interceptor_instance
    # Interceptor configuration
    interceptor_param: value
```

### Complete Example Pipeline

```yaml
# Pipeline: High-Performance I/O Benchmark
# Purpose: Measures I/O performance with profiling and tracing
name: io_benchmark_pipeline

# Pipeline-wide environment (named environment reference)
# The 'benchmark_env' should define:
#   BENCHMARK_ROOT: "/tmp/benchmark"
#   MPI_ROOT: "/usr/lib/openmpi"
#   PROFILER_OUTPUT_DIR: "/tmp/profiling"
env: benchmark_env

# Interceptors defined at pipeline level
interceptors:
  # Performance profiler interceptor
  - pkg_type: builtin.perf_profiler
    pkg_name: profiler
    sampling_rate: 1000
    output_file: "${PROFILER_OUTPUT_DIR}/perf.out"
    enable_callgraph: true
    
  # I/O tracing interceptor  
  - pkg_type: builtin.io_tracer
    pkg_name: io_monitor
    trace_reads: true
    trace_writes: true
    trace_file: "${PROFILER_OUTPUT_DIR}/io_trace.log"
    min_size: 4096

# Main pipeline packages
pkgs:
  # Setup shared filesystem
  - pkg_type: builtin.mkfs
    pkg_name: filesystem_setup
    filesystem_type: "ext4"
    mount_point: "${BENCHMARK_ROOT}"
    size: "10G"
    
  # Database service (no interceptors)
  - pkg_type: builtin.redis
    pkg_name: database
    port: 6379
    data_dir: "${BENCHMARK_ROOT}/redis_data"
    memory_limit: "2G"
    
  # I/O benchmark application (with interceptors)
  - pkg_type: builtin.ior
    pkg_name: io_benchmark
    interceptors: ["profiler", "io_monitor"]  # Apply both interceptors
    nprocs: 4
    ppn: 2
    block: "1G"
    transfer: "64K"
    test_file: "${BENCHMARK_ROOT}/ior_test_file"
    
  # Analysis application (with profiler only)
  - pkg_type: builtin.data_analysis
    pkg_name: results_analyzer
    interceptors: ["profiler"]  # Apply profiler only
    input_dir: "${PROFILER_OUTPUT_DIR}"
    output_file: "${BENCHMARK_ROOT}/analysis_results.json"
```

### Environment Types

The `env` field in a pipeline YAML must be either a **named environment reference** (string) or **omitted** (auto-build). Inline environment dictionaries are **not supported**.

#### 1. Named Environment Reference
```yaml
name: my_pipeline
env: production_environment  # References a named environment
```

**Auto-Creation**: If the named environment doesn't exist, Jarvis-CD will automatically create it by capturing the current shell environment and save it with the specified name. This allows you to reference environments that will be built on-demand.

**Creating Named Environments**: To create a named environment with custom variables:
```bash
# Create a named environment from current shell
jarvis ppl env build my_custom_env

# Or build with additional commands (e.g., module loads)
jarvis ppl env build my_custom_env module load gcc/9.3.0 openmpi/4.1.0
```

#### 2. Auto-built Environment (Default)
```yaml
name: my_pipeline
# No env field - automatically captures current environment
```

### Container Configuration

Pipelines can be configured to run all packages in a shared container environment. This is useful for reproducibility, dependency management, and multi-node deployments.

#### Container Pipeline Parameters

```yaml
name: my_containerized_pipeline

# Container configuration (all fields optional)
container_name: my_app_container                    # Container/image name (required for containerization)
container_engine: podman                            # Container engine: docker or podman (default: podman)
container_base: docker.io/iowarp/iowarp-build:latest    # Base image to build FROM
container_ssh_port: 2222                            # SSH port for container communication (default: 2222)

# Optional: Custom extensions to Docker compose file (merged into service config)
container_extensions:
  volumes:
    - /data:/data:ro                                # Mount additional volumes
  environment:
    MY_VAR: value                                   # Add environment variables
  devices:
    - /dev/nvidia0:/dev/nvidia0                     # Add device access

pkgs:
  - pkg_type: builtin.ior
    deploy_mode: container  # Use containerized deployment
    nprocs: 4
```

**Container Configuration Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `container_name` | string | `""` (not containerized) | Name for the container image. If set, enables containerization |
| `container_engine` | string | `"podman"` | Container engine to use (`docker` or `podman`) |
| `container_base` | string | `"iowarp/iowarp-build:latest"` | Base Docker image to build from |
| `container_ssh_port` | int | `2222` | SSH port for inter-container and container-host communication |
| `container_extensions` | dict | `{}` | Custom Docker Compose configuration merged into service definition |

#### How Container Pipelines Work

1. **Container Build Phase** (`jarvis ppl load yaml` or `jarvis ppl configure`):
   - Pipeline collects all packages with `deploy_mode=container`
   - Each package's `augment_container()` method adds installation commands to Dockerfile
   - Pipeline generates global Dockerfile in `~/.ppi-jarvis/containers/{container_name}.Dockerfile`
   - Container image is built and tagged as `{container_name}`
   - Manifest file tracks installed packages to avoid unnecessary rebuilds

2. **Container Deployment Phase** (`jarvis ppl start`):
   - Pipeline starts containers on all nodes in hostfile using `pssh`
   - Containers run with `network_mode: host` and `ipc: host` for performance
   - SSH daemon starts inside container for multi-node MPI communication
   - Pipeline YAML is mounted into container at `/root/.ppi-jarvis/shared/pipeline.yaml`
   - Packages execute inside container with full environment and interceptor support

3. **Container Lifecycle**:
   - `jarvis ppl start`: Brings up containers on all nodes, runs pipeline packages
   - `jarvis ppl stop`: Gracefully stops containers
   - `jarvis ppl kill`: Force terminates containers
   - `jarvis ppl clean`: Removes container data

#### Complete Container Pipeline Example

```yaml
# Pipeline: Containerized I/O Benchmark
# Purpose: Run IOR benchmark in reproducible container environment
# Requirements: Podman or Docker installed on all nodes
# Expected Runtime: 5-10 minutes (including container build)

name: ior_container_benchmark

# Auto-build environment from current shell
# No env field - will capture current environment automatically

# Container configuration
container_name: ior_benchmark_container
container_engine: podman
container_base: docker.io/iowarp/iowarp-build:latest
container_ssh_port: 2222

pkgs:
  # IOR benchmark with container deployment
  - pkg_type: builtin.ior
    pkg_name: ior_test
    # Deployment mode: 'default' for bare metal, 'container' for containerized
    deploy_mode: container
    # IOR benchmark parameters
    nprocs: 4
    ppn: 2
    block: 1G
    xfer: 1M
    api: posix
    out: /tmp/ior_test_file
    write: true
    read: true
```

#### Mixed Deployment: Bare Metal + Container

You can run some packages on bare metal and others in containers within the same pipeline:

```yaml
name: mixed_deployment_pipeline

# Container configuration for packages that need it
container_name: app_container
container_engine: docker
container_base: docker.io/iowarp/iowarp-build:latest

pkgs:
  # Run database on bare metal (better performance)
  - pkg_type: builtin.redis
    pkg_name: database
    deploy_mode: default  # Bare metal deployment
    port: 6379
    memory_limit: 8G

  # Run application in container (reproducibility)
  - pkg_type: builtin.my_app
    pkg_name: containerized_app
    deploy_mode: container  # Container deployment
    database_host: localhost
    database_port: 6379
```

#### Container Rebuild Control

Containers are automatically rebuilt when:
- Package manifest changes (packages added/removed)
- Base image changes
- First time loading a pipeline with containers

To force a rebuild:

```bash
# Rebuild specific container
jarvis container update my_container_name

# Rebuild with no cache (clean rebuild)
jarvis container update my_container_name +no_cache

# Specify container engine
jarvis container update my_container_name engine=docker

# Update pipeline and rebuild container
jarvis ppl update +container +no_cache
```

#### Container Architecture

**Global Container Storage:**
- Containers are stored globally in `~/.ppi-jarvis/containers/`
- Multiple pipelines can share the same container image
- Container images are tagged and reused across pipeline instances

**Container File Structure:**
```
~/.ppi-jarvis/containers/
├── my_container.Dockerfile     # Generated Dockerfile
├── my_container.manifest       # Package manifest (JSON)
└── compose_files/              # Per-pipeline compose files
    └── pipeline_name/
        └── docker-compose.yaml
```

**Container Features:**
- **Host Networking**: Containers use `network_mode: host` for direct network access
- **IPC Sharing**: `ipc: host` removes shared memory limits
- **Memory Limits**: Unlimited memlock and 64MB stack via ulimits
- **SSH Support**: Built-in SSH daemon for MPI multi-node communication
- **GPU Access**: Available via host networking mode (no explicit GPU configuration needed)

#### Container Best Practices

1. **Use Specific Base Images**: Specify exact image tags for reproducibility
   ```yaml
   container_base: docker.io/ubuntu:22.04  # ✅ Good - specific version
   container_base: ubuntu:latest           # ❌ Avoid - version can change
   ```

2. **Share Containers Across Pipelines**: Reuse containers with identical package sets
   ```yaml
   # Pipeline 1
   container_name: shared_ior_container

   # Pipeline 2 (reuses same container)
   container_name: shared_ior_container
   ```

3. **Test Locally Before Deployment**: Build and test containers locally first
   ```bash
   jarvis ppl load yaml my_pipeline.yaml  # Builds container
   jarvis ppl start                       # Test locally
   ```

4. **Monitor Container Resources**: Check container disk usage and clean old images
   ```bash
   podman images | grep jar  # List Jarvis containers
   podman system prune       # Clean unused containers
   ```

5. **Use Container Extensions for Custom Configuration**: Extend compose file for specific needs
   ```yaml
   container_extensions:
     # Add GPU support
     deploy:
       resources:
         reservations:
           devices:
             - driver: nvidia
               count: all
               capabilities: [gpu]
   ```

#### Container Extensions

The `container_extensions` parameter allows you to extend the generated Docker Compose service configuration with custom settings. Extensions are deep-merged into the service definition, allowing you to add or override any Docker Compose service parameters.

**Common Use Cases:**

1. **Additional Volume Mounts**:
   ```yaml
   container_extensions:
     volumes:
       - /scratch:/scratch:rw       # Scratch space
       - /datasets:/data:ro         # Read-only datasets
       - /results:/output:rw        # Output directory
   ```

2. **Environment Variables**:
   ```yaml
   container_extensions:
     environment:
       CUDA_VISIBLE_DEVICES: "0,1"
       OMP_NUM_THREADS: "16"
       PYTHONPATH: "/custom/path"
   ```

3. **Device Access** (GPU, InfiniBand, etc.):
   ```yaml
   container_extensions:
     devices:
       - /dev/nvidia0:/dev/nvidia0
       - /dev/nvidiactl:/dev/nvidiactl
       - /dev/infiniband/uverbs0:/dev/infiniband/uverbs0
   ```

4. **Resource Limits**:
   ```yaml
   container_extensions:
     deploy:
       resources:
         limits:
           cpus: '8'
           memory: 16G
         reservations:
           cpus: '4'
           memory: 8G
   ```

5. **Capabilities and Security**:
   ```yaml
   container_extensions:
     cap_add:
       - SYS_PTRACE    # For debugging
       - IPC_LOCK      # For RDMA
     security_opt:
       - seccomp:unconfined
   ```

6. **Complete GPU Configuration Example**:
   ```yaml
   name: gpu_pipeline
   container_name: gpu_app_container
   container_engine: docker
   container_base: docker.io/nvidia/cuda:12.0-base

   container_extensions:
     # Docker GPU configuration (Docker Compose v2.3+ format)
     deploy:
       resources:
         reservations:
           devices:
             - driver: nvidia
               count: all
               capabilities: [gpu, compute, utility]
     # Additional GPU environment variables
     environment:
       NVIDIA_VISIBLE_DEVICES: all
       NVIDIA_DRIVER_CAPABILITIES: compute,utility

   pkgs:
     - pkg_type: builtin.gpu_benchmark
       deploy_mode: container
   ```

**Extension Merging Behavior:**

- **Dictionaries**: Recursively merged (deep merge)
- **Lists**: Extended (items appended)
- **Scalars**: Source value overrides target value

Example merge:
```yaml
# Base configuration (generated by Jarvis)
volumes:
  - /root/.ppi-jarvis/shared:/root/.ppi-jarvis/shared

# Extension
container_extensions:
  volumes:
    - /data:/data

# Result after merge
volumes:
  - /root/.ppi-jarvis/shared:/root/.ppi-jarvis/shared
  - /data:/data
```

### Package Configuration

#### Basic Package Definition
```yaml
pkgs:
  - pkg_type: builtin.ior           # Package type (repo.package)
    pkg_name: benchmark_run         # Instance name (unique in pipeline)
    # Package-specific configuration
    nprocs: 8
    block: "2G"
    transfer: "1M"
```

#### Package with Interceptors
```yaml
pkgs:
  - pkg_type: builtin.application
    pkg_name: app_with_monitoring
    interceptors: ["profiler", "tracer"]  # List of interceptor names
    # Application configuration
    input_file: "data.txt"
    output_dir: "/tmp/results"
```

### Interceptor Configuration

#### Interceptor Definition
```yaml
interceptors:
  - pkg_type: builtin.memory_profiler    # Interceptor package type
    pkg_name: mem_profiler               # Interceptor instance name
    # Interceptor-specific configuration
    sample_interval: 100
    output_format: "json"
    detect_leaks: true
```

#### Multiple Interceptors
```yaml
interceptors:
  - pkg_type: builtin.perf_profiler
    pkg_name: cpu_profiler
    sampling_rate: 1000
    
  - pkg_type: builtin.io_tracer
    pkg_name: io_monitor
    trace_reads: true
    trace_writes: true
    
  - pkg_type: builtin.memory_debugger
    pkg_name: mem_checker
    tool: "asan"
    detect_leaks: true
```

### Advanced YAML Features

#### Environment Variable Substitution

Environment variables from named environments can be referenced in package configurations using `${VAR_NAME}` syntax:

```yaml
# Named environment should define: WORK_DIR, LOG_DIR
env: my_work_environment

pkgs:
  - pkg_type: builtin.app
    pkg_name: worker
    work_directory: "${WORK_DIR}"        # Uses WORK_DIR from named environment
    log_file: "${LOG_DIR}/worker.log"    # Uses LOG_DIR from named environment
    temp_space: "${WORK_DIR}/temp"       # Combines variables
```

#### Complex Configuration
```yaml
pkgs:
  - pkg_type: builtin.mpi_application
    pkg_name: parallel_solver
    # MPI configuration
    nprocs: 16
    ppn: 4
    # Application parameters
    solver_type: "iterative"
    tolerance: 1e-6
    max_iterations: 1000
    # File paths
    input_mesh: "/data/mesh.vtk"
    output_solution: "/results/solution.vtk"
    # Advanced options
    use_gpu: false
    memory_limit: "8G"
    checkpoint_interval: 100
```

## Pipeline CLI Commands

### Pipeline Creation and Management

#### Create New Pipeline
```bash
# Create a new empty pipeline
jarvis ppl create my_pipeline

# Creates directory: ~/.ppi-jarvis/config/pipelines/my_pipeline/
# Sets as current pipeline
```

#### Add Packages to Pipeline
```bash
# Add package to current pipeline
jarvis ppl append builtin.ior

# Add package with alias
jarvis ppl append builtin.ior benchmark_run

# Add package with full repository specification
jarvis ppl append my_repo.custom_app my_app
```

#### Remove Packages from Pipeline
```bash
# Remove package by instance name
jarvis ppl rm benchmark_run

# Remove package (shows available packages if not found)
jarvis ppl rm nonexistent_pkg
```

### Pipeline Loading and Execution

#### Load Pipeline from YAML
```bash
# Load pipeline from YAML file
jarvis ppl load yaml /path/to/pipeline.yaml

# Creates pipeline directory and sets as current
# Overwrites existing pipeline with same name
```

#### Run Pipeline (Complete Lifecycle)
```bash
# Run current pipeline (start → stop)
jarvis ppl run

# Load and run pipeline in one command
jarvis ppl run yaml /path/to/pipeline.yaml
```

#### Pipeline Lifecycle Management
```bash
# Start pipeline (run packages)
jarvis ppl start

# Stop pipeline (graceful shutdown)
jarvis ppl stop

# Force kill all pipeline processes
jarvis ppl kill

# Clean all pipeline data
jarvis ppl clean
```

### Pipeline Information and Status

#### List Available Pipelines
```bash
# List all pipelines with package counts
jarvis ppl list

# Output shows:
#   * current_pipeline (3 packages)  # * indicates current
#     other_pipeline (1 package)
#     broken_pipeline (error reading config)
```

#### Show Pipeline Configuration
```bash
# Print complete pipeline configuration
jarvis ppl print

# Shows:
# - Pipeline name and directory
# - All packages with configuration
# - All interceptors with configuration  
# - Last loaded file (if from YAML)
```

#### Check Pipeline Status
```bash
# Show status of all packages in pipeline
jarvis ppl status

# Shows:
# Pipeline: my_pipeline
# Packages:
#   database: running
#   app1: stopped
#   profiler: no status method
```

### Pipeline Switching and Destruction

#### Switch Current Pipeline
```bash
# Switch to different pipeline
jarvis cd other_pipeline

# Shows basic pipeline information after switching
```

#### Destroy Pipeline
```bash
# Destroy current pipeline
jarvis ppl destroy

# Destroy specific pipeline
jarvis ppl destroy old_pipeline

# Attempts to clean package data before destruction
# Removes entire pipeline directory
```

#### Update Pipeline from File
```bash
# Reload current pipeline from its last loaded YAML file
jarvis ppl update

# Only works if pipeline was loaded from YAML file
# Useful for development and testing
```

### Package Configuration

#### Configure Package in Pipeline
```bash
# Configure package parameters
jarvis pkg conf app_name param1=value1 param2=value2

# Configure package in specific pipeline
jarvis pkg conf pipeline.package_name param=value

# Examples:
jarvis pkg conf ior_benchmark nprocs=8 block=2G
jarvis pkg conf my_pipeline.database port=5432 memory=4G
```

#### Show Package Information
```bash
# Show package README
jarvis pkg readme package_name
jarvis pkg readme repo.package_name
jarvis pkg readme pipeline.package_name

# Show package file paths
jarvis pkg path package_name --conf --shared_dir --pkg_dir
```

### Environment Management

#### Build Pipeline Environment
```bash
# Build environment from current shell
jarvis ppl env build

# Build with additional module loading
jarvis ppl env build module load gcc/9.3.0 openmpi/4.1.0
```

#### Copy Named Environment
```bash
# Copy named environment to current pipeline
jarvis ppl env copy production_env

# Environment must exist in ~/.ppi-jarvis/config/environments/
```

#### Show Pipeline Environment
```bash
# Display current pipeline environment variables
jarvis ppl env show
```

### Pipeline Indexes

#### List Available Pipeline Scripts
```bash
# List all pipeline scripts from all repositories
jarvis ppl index list

# List scripts from specific repository
jarvis ppl index list builtin

# Output shows files and directories with color coding:
#   script.yaml                    # Default color (loadable file)
#   examples/ (directory)          # Cyan color (subdirectory)
```

#### Load Pipeline from Index
```bash
# Load pipeline script directly
jarvis ppl index load builtin.examples.simple_test

# Load from nested directory
jarvis ppl index load my_repo.benchmarks.io_tests.ior_benchmark
```

#### Copy Pipeline Script
```bash
# Copy to current directory
jarvis ppl index copy builtin.examples.simple_test

# Copy to specific location
jarvis ppl index copy builtin.examples.simple_test /tmp/

# Copy with custom filename
jarvis ppl index copy builtin.examples.simple_test ./my_pipeline.yaml
```

## Pipeline Lifecycle

Understanding the pipeline lifecycle helps with debugging and optimization.

### 1. Pipeline Creation/Loading

```bash
jarvis ppl create my_pipeline
# OR
jarvis ppl load yaml pipeline.yaml
```

**Actions Performed:**
- Create pipeline directory: `~/.ppi-jarvis/config/pipelines/my_pipeline/`
- Generate `pipeline.yaml` with pipeline configuration
- Generate `env.yaml` with environment variables
- Set as current pipeline in Jarvis configuration
- Create package subdirectories for each package

### 2. Package Addition

```bash
jarvis ppl append builtin.ior benchmark
```

**Actions Performed:**
- Validate package exists in repositories
- Create package directory: `packages/benchmark/`
- Load package defaults from package's `configure_menu()`
- Generate package configuration entry in `pipeline.yaml`
- Create package subdirectories: `config/`, `shared/`, `private/`

### 3. Package Configuration

```bash
jarvis pkg conf benchmark nprocs=4 block=1G
```

**Actions Performed:**
- Load package instance with current configuration
- Apply type conversion to configuration parameters
- Update package configuration in `pipeline.yaml`
- Call package's `configure()` method
- Generate package-specific configuration files in `config/`

### 4. Pipeline Execution

```bash
jarvis ppl start
```

**Actions Performed:**
- Load pipeline configuration and environment
- For each package in sequence:
  - Load package instance with pipeline environment
  - Apply interceptors (if any):
    - Load interceptor instances
    - Share `mod_env` reference between interceptor and package
    - Call interceptor's `modify_env()` method
  - Call package's `start()` method
  - Propagate environment changes to next packages

### 5. Pipeline Stopping

```bash
jarvis ppl stop
```

**Actions Performed:**
- Load pipeline configuration
- For each package in reverse order:
  - Load package instance
  - Call package's `stop()` method

### 6. Pipeline Cleanup

```bash
jarvis ppl clean
```

**Actions Performed:**
- For each package:
  - Load package instance
  - Call package's `clean()` method
  - Remove temporary files and data

## Environment Management

Environment variables are central to pipeline coordination and package communication.

### Environment Hierarchy

1. **System Environment**: Current shell environment variables
2. **Named Environment**: Predefined environment loaded from `~/.ppi-jarvis/config/environments/`
3. **Pipeline Environment**: Pipeline-specific environment in `env.yaml`
4. **Package Environment**: Package-specific environment modifications

### Environment Propagation

```
System Env → Named/Pipeline Env → Package 1 → Package 2 → Package 3
     ↓              ↓                ↓           ↓           ↓
  PATH=...      CC=gcc-9      PATH+=app1/bin  PATH+=app2  CUSTOM_VAR=val
```

### Environment Variable Types

#### Package Environment (`pkg.env`)
- Contains all environment variables except `LD_PRELOAD`
- Shared across packages in pipeline
- Changes propagated to subsequent packages
- Used for: library paths, application settings, build configuration

#### Modified Environment (`pkg.mod_env`)
- Exact copy of `pkg.env` plus `LD_PRELOAD`
- Private to each package instance
- Modified by interceptors
- Used for: package execution, interceptor injection

### Environment Examples

#### Building Custom Environment
```bash
# Start with clean environment
jarvis ppl env build

# Add development tools
jarvis ppl env build \
  module load gcc/9.3.0 \
  module load openmpi/4.1.0 \
  export CUDA_ROOT=/usr/local/cuda
```

#### Pipeline Environment Configuration

Instead of inline environment dictionaries, use named environments:

```bash
# First, create a named environment with your custom variables
# This can be done by setting environment variables in your shell, then:
export CC="/usr/bin/gcc-9"
export CXX="/usr/bin/g++-9"
export LD_LIBRARY_PATH="/opt/intel/lib:${LD_LIBRARY_PATH}"
export OMP_NUM_THREADS="4"
export CUDA_VISIBLE_DEVICES="0,1"
export BENCHMARK_DATA_DIR="/data/benchmarks"
export RESULTS_OUTPUT_DIR="/tmp/results"

# Build a named environment from your current shell
jarvis ppl env build my_pipeline_env
```

```yaml
# In pipeline YAML, reference the named environment
name: my_pipeline
env: my_pipeline_env  # References the environment created above
```

#### Package Environment Modification
```python
# In package configure() method
def _configure(self, **kwargs):
    # Add application-specific paths
    self.setenv('MY_APP_HOME', '/opt/myapp')
    self.prepend_env('PATH', '/opt/myapp/bin')
    self.prepend_env('LD_LIBRARY_PATH', '/opt/myapp/lib')
    
    # Set application configuration
    self.setenv('MY_APP_CONFIG', f'{self.shared_dir}/app.conf')
    self.setenv('MY_APP_LOG_LEVEL', 'INFO')
```

## Pipeline Indexes

Pipeline indexes provide discoverable, reusable pipeline templates and examples.

### Index Structure in Repositories

```
my_repo/
├── my_repo/                    # Package source code
│   ├── package1/
│   └── package2/
└── pipelines/                  # Pipeline index
    ├── basic_example.yaml
    ├── benchmarks/
    │   ├── io_test.yaml
    │   └── compute_test.yaml
    └── tutorials/
        ├── getting_started.yaml
        └── advanced_features.yaml
```

### Using Pipeline Indexes

#### Discovery
```bash
# List all available pipeline scripts
jarvis ppl index list

# Output:
# Available pipeline scripts:
#   builtin:
#     simple_test.yaml
#     test_interceptor.yaml
#     examples/ (directory)
#       basic_workflow.yaml
#       advanced_demo.yaml
```

#### Loading
```bash
# Load pipeline directly into current workspace
jarvis ppl index load builtin.examples.basic_workflow

# Creates new pipeline from the template
# Sets as current pipeline
```

#### Copying for Customization
```bash
# Copy pipeline script for modification
jarvis ppl index copy builtin.examples.basic_workflow ./my_custom.yaml

# Edit the copied file
vim my_custom.yaml

# Load your customized version
jarvis ppl load yaml ./my_custom.yaml
```

### Creating Pipeline Index Entries

#### Example Index Pipeline
```yaml
# File: pipelines/examples/basic_io_benchmark.yaml
# Pipeline: Basic I/O Performance Test
# Purpose: Simple I/O benchmark with monitoring
# Requirements: MPI environment, named environment 'io_test_env' with TEST_DIR and BLOCK_SIZE
# Expected Runtime: 5-10 minutes

name: basic_io_benchmark
# Named environment should define: TEST_DIR="/tmp/io_test", BLOCK_SIZE="1G"
env: io_test_env

interceptors:
  - pkg_type: builtin.io_tracer
    pkg_name: io_monitor
    trace_reads: true
    trace_writes: true
    output_file: "${TEST_DIR}/io_trace.log"

pkgs:
  - pkg_type: builtin.mkfs
    pkg_name: setup_filesystem
    mount_point: "${TEST_DIR}"
    size: "10G"
    
  - pkg_type: builtin.ior
    pkg_name: io_benchmark
    interceptors: ["io_monitor"]
    nprocs: 4
    block: "${BLOCK_SIZE}"
    test_file: "${TEST_DIR}/test_file"
```

## Advanced Pipeline Features

### Multi-Stage Pipelines

```yaml
name: multi_stage_pipeline

pkgs:
  # Stage 1: Data preparation
  - pkg_type: builtin.data_generator
    pkg_name: data_prep
    data_size: "100G"
    output_dir: "/tmp/data"
    
  # Stage 2: Parallel processing
  - pkg_type: builtin.mpi_processor
    pkg_name: parallel_analysis
    input_dir: "/tmp/data"          # Uses output from stage 1
    nprocs: 16
    
  # Stage 3: Results aggregation
  - pkg_type: builtin.aggregator
    pkg_name: results_summary
    input_pattern: "/tmp/data/results_*"
    output_file: "/tmp/final_results.json"
```

### Conditional Package Execution

```yaml
name: conditional_pipeline

pkgs:
  # Always runs
  - pkg_type: builtin.system_check
    pkg_name: prerequisites
    
  # Runs only if GPU available
  - pkg_type: builtin.gpu_benchmark
    pkg_name: gpu_test
    enable_condition: "has_cuda"
    
  # Fallback for non-GPU systems
  - pkg_type: builtin.cpu_benchmark
    pkg_name: cpu_test
    enable_condition: "no_cuda"
```

### Complex Interceptor Combinations

```yaml
name: comprehensive_monitoring

interceptors:
  # CPU profiling
  - pkg_type: builtin.perf_profiler
    pkg_name: cpu_profiler
    sampling_rate: 1000
    
  # Memory debugging
  - pkg_type: builtin.memory_debugger
    pkg_name: mem_checker
    tool: "asan"
    
  # I/O monitoring
  - pkg_type: builtin.io_tracer
    pkg_name: io_monitor
    trace_all: true
    
  # Network monitoring
  - pkg_type: builtin.network_tracer
    pkg_name: net_monitor
    trace_mpi: true

pkgs:
  # Lightweight application (minimal monitoring)
  - pkg_type: builtin.simple_app
    pkg_name: lightweight
    interceptors: ["io_monitor"]
    
  # Intensive application (full monitoring)
  - pkg_type: builtin.complex_app
    pkg_name: intensive
    interceptors: ["cpu_profiler", "mem_checker", "io_monitor", "net_monitor"]
    
  # Debug version (memory checking only)
  - pkg_type: builtin.debug_app
    pkg_name: debug_version
    interceptors: ["mem_checker"]
```

## Best Practices

### Pipeline Design

#### 1. Use Descriptive Names
```yaml
# ✅ Good
name: hpc_io_performance_benchmark

# ❌ Poor
name: test
```

#### 2. Organize by Logical Stages
```yaml
pkgs:
  # Setup stage
  - pkg_type: builtin.environment_setup
    pkg_name: env_setup
    
  - pkg_type: builtin.data_preparation
    pkg_name: data_prep
    
  # Execution stage
  - pkg_type: builtin.benchmark
    pkg_name: main_benchmark
    
  # Cleanup stage
  - pkg_type: builtin.results_collector
    pkg_name: cleanup
```

#### 3. Use Environment Variables for Paths

Define paths in a named environment, then reference them in package configurations:

```yaml
# Named environment should define: WORK_DIR="/scratch/benchmark", RESULTS_DIR="/home/user/results"
env: benchmark_paths_env

pkgs:
  - pkg_type: builtin.app
    pkg_name: processor
    input_dir: "${WORK_DIR}/input"
    output_dir: "${RESULTS_DIR}/output"
```

### Configuration Management

#### 1. Provide Reasonable Defaults
```yaml
pkgs:
  - pkg_type: builtin.ior
    pkg_name: io_test
    # Provide sensible defaults
    nprocs: 4
    block: "1G"
    transfer: "64K"
    # Allow easy customization
    test_file: "${WORK_DIR}/test_file"
```

#### 2. Document Complex Parameters
```yaml
pkgs:
  - pkg_type: builtin.solver
    pkg_name: numerical_solver
    # Solver configuration
    method: "gmres"              # Options: gmres, bicgstab, cg
    tolerance: 1e-6              # Convergence tolerance
    max_iterations: 1000         # Maximum solver iterations
    preconditioner: "ilu"        # Preconditioning method
```

#### 3. Use Type-Appropriate Values
```yaml
pkgs:
  - pkg_type: builtin.app
    pkg_name: configured_app
    # Integer parameters
    nprocs: 8                    # Not "8"
    port: 5432                   # Not "5432"
    # Boolean parameters  
    enable_debug: true           # Not "true"
    use_gpu: false              # Not "false"
    # String parameters
    log_level: "INFO"           # Quoted for clarity
    output_format: "json"       # Quoted for clarity
```

### Interceptor Usage

#### 1. Apply Interceptors Selectively
```yaml
interceptors:
  - pkg_type: builtin.profiler
    pkg_name: perf_monitor

pkgs:
  # Only monitor performance-critical packages
  - pkg_type: builtin.fast_app
    pkg_name: critical_app
    interceptors: ["perf_monitor"]    # Apply monitoring
    
  # Skip monitoring for simple utilities
  - pkg_type: builtin.file_copy
    pkg_name: file_util
    # No interceptors - lightweight operation
```

#### 2. Group Related Interceptors
```yaml
interceptors:
  # Performance monitoring group
  - pkg_type: builtin.cpu_profiler
    pkg_name: cpu_monitor
  - pkg_type: builtin.memory_profiler  
    pkg_name: mem_monitor
    
  # I/O monitoring group
  - pkg_type: builtin.io_tracer
    pkg_name: io_monitor

pkgs:
  - pkg_type: builtin.compute_app
    pkg_name: cpu_intensive
    interceptors: ["cpu_monitor", "mem_monitor"]
    
  - pkg_type: builtin.io_app
    pkg_name: io_intensive
    interceptors: ["io_monitor"]
```

### Environment Management

#### 1. Minimize Environment Pollution

When creating named environments, be specific and avoid overwriting critical system variables:

```bash
# ✅ Good - specific and necessary
export BENCHMARK_DATA_DIR="/data/benchmark"
export RESULTS_OUTPUT_DIR="/tmp/results"
jarvis ppl env build clean_benchmark_env

# ❌ Poor - overwrites important system variables
export PATH="/my/custom/path"           # Loses system PATH - dangerous!
export LD_LIBRARY_PATH="/my/libs"       # Overwrites system libraries - dangerous!
jarvis ppl env build problematic_env    # Don't do this!
```

#### 2. Use Environment Composition

When building named environments, compose paths properly:

```bash
# Define base directories
export PROJECT_ROOT="/opt/myproject"
export DATA_ROOT="/data"

# Build derived paths
export PROJECT_BIN="${PROJECT_ROOT}/bin"
export PROJECT_LIB="${PROJECT_ROOT}/lib"

# Extend system paths (don't replace them!)
export PATH="${PROJECT_BIN}:${PATH}"
export LD_LIBRARY_PATH="${PROJECT_LIB}:${LD_LIBRARY_PATH}"

# Save as named environment
jarvis ppl env build composed_project_env
```

### Error Handling

#### 1. Validate Prerequisites
```yaml
pkgs:
  # Check system requirements first
  - pkg_type: builtin.system_check
    pkg_name: prerequisites
    required_memory: "8G"
    required_disk: "100G"
    required_commands: ["mpiexec", "gcc"]
    
  # Main application
  - pkg_type: builtin.main_app
    pkg_name: application
```

#### 2. Provide Cleanup Stages
```yaml
pkgs:
  # Setup
  - pkg_type: builtin.setup
    pkg_name: initialization
    
  # Main work
  - pkg_type: builtin.application
    pkg_name: main_work
    
  # Always cleanup (even on failure)
  - pkg_type: builtin.cleanup
    pkg_name: cleanup
    run_on_failure: true
```

## Troubleshooting

### Common Issues and Solutions

#### Pipeline Loading Failures

**Problem**: `jarvis ppl load yaml pipeline.yaml` fails
```
Error: Package not found: my_repo.custom_app
```

**Solutions**:
1. Verify repository is added: `jarvis repo list`
2. Add repository: `jarvis repo add /path/to/my_repo`
3. Check package exists: `jarvis ppl append my_repo.custom_app` (test)

**Problem**: YAML syntax errors
```
Error: yaml.scanner.ScannerError: while parsing a block mapping
```

**Solutions**:
1. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('pipeline.yaml'))"`
2. Check indentation (use spaces, not tabs)
3. Quote string values with special characters

#### Package Configuration Issues

**Problem**: Package configuration not applied
```
jarvis pkg conf app param=value
# Parameter not updated in pipeline
```

**Solutions**:
1. Check parameter name: `jarvis pkg conf app --help`
2. Use correct type: `jarvis pkg conf app count=5` (not `count="5"` for integer)
3. Verify package exists in current pipeline: `jarvis ppl print`

#### Environment Problems

**Problem**: Environment variables not propagated
```
Package can't find libraries despite setting LD_LIBRARY_PATH
```

**Solutions**:
1. Set environment in pipeline YAML, not package configuration
2. Use `_configure()` method in package code for environment changes
3. Check environment propagation: `jarvis ppl env show`

#### Interceptor Issues

**Problem**: Interceptor not applied
```
jarvis ppl start
# No profiling output despite interceptor configuration
```

**Solutions**:
1. Verify interceptor exists in pipeline: `jarvis ppl print`
2. Check package references interceptor: look for `interceptors: ["interceptor_name"]`
3. Ensure interceptor package implements `modify_env()` method

### Debugging Commands

#### Check Pipeline State
```bash
# Show complete pipeline configuration
jarvis ppl print

# Check package configuration
jarvis pkg conf package_name --help

# Show package paths
jarvis pkg path package_name --conf_dir --shared_dir
```

#### Environment Debugging
```bash
# Show pipeline environment
jarvis ppl env show

# Check current pipeline
jarvis ppl list

# Show package environment files
jarvis pkg path package_name --env --mod_env
```

#### Process Debugging
```bash
# Check pipeline status
jarvis ppl status

# Show running processes
ps aux | grep jarvis

# Check package logs
tail -f ~/.ppi-jarvis/config/pipelines/my_pipeline/packages/app/shared/*.log
```

### Performance Optimization

#### Pipeline Execution Performance

1. **Minimize Package Count**: Combine related operations into single packages
2. **Optimize Environment**: Reduce environment variable propagation overhead
3. **Selective Interceptors**: Apply interceptors only where needed
4. **Parallel Packages**: Use MPI for parallel execution within packages

#### Storage Optimization

1. **Clean Regularly**: Use `jarvis ppl clean` to remove temporary files
2. **Monitor Disk Usage**: Check pipeline directory sizes
3. **Use Shared Storage**: Place large datasets in shared directories
4. **Archive Old Pipelines**: Remove unused pipeline directories

This comprehensive documentation covers all aspects of pipeline management in Jarvis-CD, from basic concepts to advanced troubleshooting. Use it as a reference for developing, debugging, and optimizing your computational pipelines.