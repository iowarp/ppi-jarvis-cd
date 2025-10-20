"""
Container-based IOR deployment using Docker/Podman compose.
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo
from jarvis_cd.shell.container_compose_exec import ContainerComposeExec, ContainerBuildExec
from jarvis_cd.shell.container_exec import ContainerExec
import os
import yaml
from pathlib import Path


class IorContainer(Application):
    """
    Container-based IOR deployment.
    """

    def _init(self):
        """
        Initialize paths
        """
        pass

    def _configure(self, **kwargs):
        """
        Configure container deployment by generating pipeline YAML,
        Dockerfile, and compose file, then build the container image.

        :param kwargs: Configuration parameters for this pkg.
        :return: None
        """
        # Call parent configuration
        super()._configure(**kwargs)

        # Generate pipeline YAML file
        self._generate_pipeline_yaml()

        # Generate Dockerfile
        self._generate_dockerfile()

        # Generate compose file
        self._generate_compose_file()

        # Build the container image
        self._build_image()

    def _generate_pipeline_yaml(self):
        """
        Generate pipeline YAML file containing just this package.
        """
        # Get this package's configuration and interceptors
        pkg_config = self.config.copy()

        # Build package entry
        pkg_entry = {'pkg_type': 'builtin.ior'}

        # Add all config parameters
        for key, value in pkg_config.items():
            if key != 'deploy':  # Exclude deploy parameter
                pkg_entry[key] = value

        # Create pipeline structure
        pipeline_config = {
            'name': f'{self.pipeline.name}_container',
            'pkgs': [pkg_entry]
        }

        # Add interceptors if any
        interceptors_list = pkg_config.get('interceptors', [])
        if interceptors_list:
            pipeline_config['interceptors'] = []
            for interceptor_name in interceptors_list:
                if interceptor_name in self.pipeline.interceptors:
                    interceptor_def = self.pipeline.interceptors[interceptor_name]
                    interceptor_entry = {
                        'pkg_type': interceptor_def['pkg_type']
                    }
                    # Add config parameters
                    for key, value in interceptor_def.get('config', {}).items():
                        interceptor_entry[key] = value
                    pipeline_config['interceptors'].append(interceptor_entry)

        # Write pipeline file to shared directory
        pipeline_file = Path(self.shared_dir) / 'pkg.yaml'
        with open(pipeline_file, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False)

        print(f"Generated pipeline YAML: {pipeline_file}")

    def _generate_dockerfile(self):
        """
        Generate Dockerfile for IOR container.
        """
        dockerfile_content = """FROM iowarp/iowarp-deps:ai

# Disable prompt during packages installation.
ARG DEBIAN_FRONTEND=noninteractive

# Install ior.
RUN . "${SPACK_DIR}/share/spack/setup-env.sh" && \\
    spack install -y ior

# Copy required spack executables and libraries to /usr
RUN . "${SPACK_DIR}/share/spack/setup-env.sh" && \\
    spack load iowarp && \\
    cp -r $(spack location -i python)/bin/* /usr/bin || true && \\
    cp -r $(spack location -i py-pip)/bin/* /usr/bin || true && \\
    cp -r $(spack location -i python-venv)/bin/* /usr/bin || true && \\
    PYTHON_PATH=$(readlink -f /usr/bin/python3) && \\
    PYTHON_PREFIX=$(dirname $(dirname $PYTHON_PATH)) && \\
    cp -r $(spack location -i mpi)/bin/* /usr/bin || true && \\
    cp -r $(spack location -i ior)/bin/* /usr/bin || true && \\
    cp -r $(spack location -i iowarp-runtime)/bin/* /usr/bin || true && \\
    cp -r $(spack location -i iowarp-cte)/bin/* /usr/bin || true && \\
    cp -r $(spack location -i cte-hermes-shm)/bin/* /usr/bin || true && \\
    for pkg in $(spack find --format '{name}' | grep '^py-'); do \\
        cp -r $(spack location -i $pkg)/lib/* $PYTHON_PREFIX/lib/ 2>/dev/null || true; \\
        cp -r $(spack location -i $pkg)/bin/* /usr/bin 2>/dev/null || true; \\
    done && \\
    sed -i '1s|.*|#!/usr/bin/python3|' /usr/bin/jarvis && \\
    echo "Spack packages copied to /usr directory"

# Copy pipeline file from shared directory into container
COPY pkg.yaml /pkg.yaml

# Load pipeline on container start
RUN jarvis ppl load yaml /pkg.yaml
"""

        dockerfile_path = Path(self.shared_dir) / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        print(f"Generated Dockerfile: {dockerfile_path}")

    def _generate_compose_file(self):
        """
        Generate docker/podman compose file.
        """
        container_name = f"{self.pipeline.name}_{self.pkg_id}"

        # Mount host directories to Jarvis default paths in container
        # Private: ~/.ppi-jarvis/private -> /root/.ppi-jarvis/private
        # Shared: ~/.ppi-jarvis/shared -> /root/.ppi-jarvis/shared
        compose_config = {
            'services': {
                'ior': {
                    'build': str(self.shared_dir),
                    'container_name': container_name,
                    'entrypoint': ['/bin/bash', '-c'],
                    'command': ['tail -f /dev/null'],
                    'volumes': [
                        f"{self.private_dir}:/root/.ppi-jarvis/private",
                        f"{self.shared_dir}:/root/.ppi-jarvis/shared"
                    ]
                }
            }
        }

        # Add IPC configuration if pipeline has shm_container
        if self.pipeline.shm_container:
            compose_config['services']['ior']['ipc'] = f"container:{self.pipeline.shm_container}"

        # Write compose file to shared directory
        compose_file = Path(self.shared_dir) / 'compose.yaml'
        with open(compose_file, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)

        print(f"Generated compose file: {compose_file}")

    def _build_image(self):
        """
        Build the container image using compose build.

        :return: None
        """
        compose_file = Path(self.shared_dir) / 'compose.yaml'

        if not compose_file.exists():
            raise FileNotFoundError(f"Compose file not found: {compose_file}")

        # Determine container runtime from config
        prefer_podman = (self.config.get('deploy') == 'podman')

        # Build the image
        print(f"Building container image from {compose_file}")
        ContainerBuildExec(
            str(compose_file),
            LocalExecInfo(env=self.mod_env),
            prefer_podman=prefer_podman
        ).run()
        print("Container image built successfully")

    def start(self):
        """
        Start the IOR container using compose, then execute jarvis ppl start inside it.

        :return: None
        """
        compose_file = Path(self.shared_dir) / 'compose.yaml'

        if not compose_file.exists():
            raise FileNotFoundError(f"Compose file not found: {compose_file}. Run configure first.")

        # Determine container runtime from config
        prefer_podman = (self.config.get('deploy') == 'podman')

        # Execute compose up (will automatically use -d flag for detached mode)
        ContainerComposeExec(
            str(compose_file),
            LocalExecInfo(env=self.mod_env),
            action='up',
            prefer_podman=prefer_podman
        ).run()

        # Get container name
        container_name = f"{self.pipeline.name}_{self.pkg_id}"
        
        # Execute jarvis ppl start inside the container
        print(f"Executing 'jarvis ppl start' inside container {container_name}")
        ContainerExec(
            container_name,
            "jarvis ppl start",
            LocalExecInfo(env=self.mod_env),
            prefer_podman=prefer_podman
        ).run()

    def stop(self):
        """
        Stop the IOR container.

        :return: None
        """
        compose_file = Path(self.shared_dir) / 'compose.yaml'

        if not compose_file.exists():
            print(f"Compose file not found: {compose_file}")
            return

        # Determine container runtime from config
        prefer_podman = (self.config.get('deploy') == 'podman')

        # Execute compose down
        ContainerComposeExec(
            str(compose_file),
            LocalExecInfo(env=self.mod_env),
            action='down',
            prefer_podman=prefer_podman
        ).run()

    def clean(self):
        """
        Clean container data.

        :return: None
        """
        # Stop containers first
        self.stop()

        # Remove generated files from shared directory
        for filename in ['pkg.yaml', 'Dockerfile', 'compose.yaml']:
            filepath = Path(self.shared_dir) / filename
            if filepath.exists():
                filepath.unlink()
                print(f"Removed {filepath}")
