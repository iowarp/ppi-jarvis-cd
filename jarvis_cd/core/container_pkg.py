"""
Base classes for containerized application deployment.
"""
from .pkg import Application
from ..shell import Exec, LocalExecInfo
from ..shell.container_compose_exec import ContainerComposeExec, ContainerBuildExec
from ..shell.container_exec import ContainerExec
import os
import yaml
from pathlib import Path


class ContainerApplication(Application):
    """
    Base class for containerized application deployment using Docker/Podman.

    This class provides common functionality for deploying applications in containers,
    including pipeline YAML generation, Dockerfile creation, and container lifecycle management.
    """

    def _init(self):
        """
        Initialize paths
        """
        pass

    def _generate_container_ppl_yaml(self):
        """
        Generate pipeline YAML file containing just this package.
        This is used to load the pipeline configuration inside the container.
        """
        # Get this package's configuration and interceptors
        pkg_config = self.config.copy()

        # Build package entry - use the actual package type
        pkg_entry = {'pkg_type': self.pkg_type}

        # Add all config parameters except 'deploy'
        for key, value in pkg_config.items():
            if key != 'deploy':
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
        Generate Dockerfile for the container.
        Subclasses should override this method to provide application-specific Dockerfile content.

        :return: None
        """
        raise NotImplementedError("Subclasses must implement _generate_dockerfile()")

    def _get_container_command(self):
        """
        Get the command to run in the container.
        Subclasses can override this to provide application-specific startup commands.

        :return: List representing the container command
        """
        ssh_port = self.config.get('deploy_ssh_port', 2222)

        # Default command: setup SSH and keep container running
        return [
            f'cp -r /root/.ssh_host /root/.ssh && '
            f'chmod 700 /root/.ssh && '
            f'chmod 600 /root/.ssh/* 2>/dev/null || true && '
            f'cat /root/.ssh/*.pub > /root/.ssh/authorized_keys 2>/dev/null && '
            f'chmod 600 /root/.ssh/authorized_keys 2>/dev/null || true && '
            f'echo "Host *" > /root/.ssh/config && '
            f'echo "    Port {ssh_port}" >> /root/.ssh/config && '
            f'echo "    StrictHostKeyChecking no" >> /root/.ssh/config && '
            f'chmod 600 /root/.ssh/config && '
            f'/usr/sbin/sshd && tail -f /dev/null'
        ]

    def _get_service_name(self):
        """
        Get the service name for the compose file.
        Subclasses can override this to provide a custom service name.

        :return: Service name string
        """
        # Use package name from pkg_type (e.g., 'builtin.ior' -> 'ior')
        if self.pkg_type and '.' in self.pkg_type:
            return self.pkg_type.split('.')[-1]
        return 'app'

    def _generate_compose_file(self):
        """
        Generate docker/podman compose file.
        Generates a standard compose configuration that works for most containerized applications.

        :return: None
        """
        container_name = f"{self.pipeline.name}_{self.pkg_id}"
        service_name = self._get_service_name()
        shm_size = self.config.get('shm_size', 0)

        # Mount host directories to Jarvis default paths in container
        ssh_dir = os.path.expanduser('~/.ssh')

        compose_config = {
            'services': {
                service_name: {
                    'build': str(self.shared_dir),
                    'container_name': container_name,
                    'entrypoint': ['/bin/bash', '-c'],
                    'command': self._get_container_command(),
                    'volumes': [
                        f"{self.private_dir}:/root/.ppi-jarvis/private",
                        f"{self.shared_dir}:/root/.ppi-jarvis/shared",
                        f"{ssh_dir}:/root/.ssh_host:ro"  # Mount SSH keys
                    ]
                }
            }
        }

        # Always use host network mode for multi-node MPI support
        compose_config['services'][service_name]['network_mode'] = 'host'

        # Handle shared memory configuration
        if shm_size > 0:
            # This container creates a new shared memory segment
            compose_config['services'][service_name]['shm_size'] = f'{shm_size}m'
            # Set this container as the shm provider for the pipeline
            self.pipeline.shm_container = container_name
            print(f"Created shared memory segment: {shm_size}MB in container {container_name}")
        elif hasattr(self.pipeline, 'shm_container') and self.pipeline.shm_container:
            # This container connects to an existing shared memory segment
            compose_config['services'][service_name]['ipc'] = f"container:{self.pipeline.shm_container}"
            print(f"Connecting to shared memory container: {self.pipeline.shm_container}")

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
        Start the container using compose, then execute jarvis ppl start inside it.

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
        Stop the container.

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


class ContainerService(ContainerApplication):
    """
    Alias for ContainerApplication following service naming conventions.

    This class is identical to ContainerApplication but follows the naming convention
    where long-running containerized applications are called "services".
    """
    pass
