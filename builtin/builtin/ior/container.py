"""
Container-based IOR deployment using Docker/Podman compose.
"""
from jarvis_cd.core.container_pkg import ContainerApplication
from pathlib import Path


class IorContainer(ContainerApplication):
    """
    Container-based IOR deployment.
    """

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
        self._generate_container_ppl_yaml()

        # Generate Dockerfile
        self._generate_dockerfile()

        # Generate compose file
        self._generate_compose_file()

        # Build the container image
        self._build_image()

    def _generate_dockerfile(self):
        """
        Generate Dockerfile for IOR container.
        """
        ssh_port = self.config.get('deploy_ssh_port', 2222)

        # sshd always listens on the configured port inside the container
        # - For host network: sshd listens directly on this port
        # - For port mapping: sshd listens on this port, gets mapped to host
        sshd_port = ssh_port

        dockerfile_content = f"""FROM iowarp/iowarp-deps:ai

# Disable prompt during packages installation.
ARG DEBIAN_FRONTEND=noninteractive

# Install ior.
RUN . "${{SPACK_DIR}}/share/spack/setup-env.sh" && \\
    spack install -y ior

# Copy required spack executables and libraries to /usr
RUN . "${{SPACK_DIR}}/share/spack/setup-env.sh" && \\
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
    for pkg in $(spack find --format '{{name}}' | grep '^py-'); do \\
        cp -r $(spack location -i $pkg)/lib/* $PYTHON_PREFIX/lib/ 2>/dev/null || true; \\
        cp -r $(spack location -i $pkg)/bin/* /usr/bin 2>/dev/null || true; \\
    done && \\
    sed -i '1s|.*|#!/usr/bin/python3|' /usr/bin/jarvis && \\
    echo "Spack packages copied to /usr directory"

# Configure SSH daemon to listen on port {sshd_port}
RUN sed -i 's/^#*Port .*/Port {sshd_port}/' /etc/ssh/sshd_config

# Copy pipeline file from shared directory into container
COPY pkg.yaml /pkg.yaml

# Load pipeline on container start
RUN jarvis ppl load yaml /pkg.yaml
"""

        dockerfile_path = Path(self.shared_dir) / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        print(f"Generated Dockerfile: {dockerfile_path}")
