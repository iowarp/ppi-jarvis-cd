@CLAUDE.md 

Add support for containerized applications. Create the following Exec (inherit from Exec):
PodmanComposeExec, DockerComposeExec, ContainerComposeExec. These are wrappers around 
docker compose and podman compose functions. ContainerCompose is simply a router that
calls one or the other. Each of them inherit from Exec.

In general, the container name should be "pipeline_name_pkg_name".

## IOR Example Update

For now, let us only change the ior package.

For the ior package, let's add a new parameter called "deploy". It is a string with the following choices: default, podman, docker.

We will have the following python files: pkg.py (the router), default.py (the default path), and container.py (the path for podman/docker).

The container.py should have the following

### Configure (container.py)

This will produce a pipeline, container, podman-compose file. 
Store a template of these two files.
The container should inherit from iowarp/iowarp-build:latest and install ior with spack. This has spack installed already.

The pipeline, dockerfile, and compose file should be placed in the private directory for the package.

#### Pipeline (YAML)
Should contain this package and all parameters to this package, including interceptors. Essentially, 
reconstruct a pipeline file containing just a single package in the pkgs: key and as many interceptors
as defined for the package.

#### Dockerfile
```
FROM iowarp/iowarp-build:latest

# Disable prompt during packages installation.
ARG DEBIAN_FRONTEND=noninteractive

# Install ior.
RUN . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack install -y ior

# Copy required spack executables to /usr so no need to do spack load in future.
RUN . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack load ior && \
    cp $(which ior) /usr/bin
    cp $(which mpi) /usr/bin

# Copy required spack executables to /usr so no need to do spack load in future.
RUN jarvis ppl load yaml /pkg.yaml
```

### Compose file

This file should expose the ior package and the priv_dir and shared_dir. 
It should connect to a container named iowarp_runtime.
```
services:
  ior: 
    image_name: .
    container_name: [PPL_NAME_PKG_NAME]

    # CRITICAL: This ensures the writer container's IPC namespace can be joined
    # by other, external containers.
    ipc: container:[PPL_NAME_iowarp_runtime]
```

The ipc command should be used only if there is an interceptor in the pipeline that requires
shared memory. Let's add a new pipeline property called shm_container and shm_size to Pipeline.
By default, shm_container is None and shm_size is 8g. If shm_container is None, the compose
file should not have an ipc: section.

## Run

Run should use ContainerComposeExec to launch the produced compose file stored in the shared directory
of the package.
