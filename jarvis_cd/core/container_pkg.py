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

        Note: This method is deprecated for pipeline-level containers.
        Use pipeline.container_ssh_port instead.

        :return: List representing the container command
        """
        # Use pipeline-level SSH port if available, otherwise fallback to default
        ssh_port = getattr(self.pipeline, 'container_ssh_port', 2222)

        # Default command: setup SSH, start sshd, run pipeline, and keep container running
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
            f'sed -i "s/^#*Port .*/Port {ssh_port}/" /etc/ssh/sshd_config && '
            f'/usr/sbin/sshd && '
            f'jarvis ppl run yaml /root/.ppi-jarvis/shared/pkg.yaml && '
            f'tail -f /dev/null'
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

        # Use global container image if pipeline has container_build or container_image, otherwise build from local Dockerfile
        if hasattr(self.pipeline, 'get_container_image') and self.pipeline.get_container_image():
            compose_config['services'][service_name]['image'] = self.pipeline.get_container_image()
        else:
            compose_config['services'][service_name]['build'] = str(self.shared_dir)

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
        Note: This is no longer used for per-package builds. Container building happens at pipeline level.

        :return: None
        """
        pass

    def start(self):
        """
        Start is handled at the pipeline level for containerized applications.
        Individual packages do not start containers themselves.

        :return: None
        """
        pass

    def stop(self):
        """
        Stop is handled at the pipeline level for containerized applications.
        Individual packages do not stop containers themselves.

        :return: None
        """
        pass

    def clean(self):
        """
        Clean is handled at the pipeline level for containerized applications.
        Individual packages do not clean containers themselves.

        :return: None
        """
        pass

    def kill(self):
        """
        Kill is handled at the pipeline level for containerized applications.
        Individual packages do not kill containers themselves.

        :return: None
        """
        pass


class ContainerService(ContainerApplication):
    """
    Alias for ContainerApplication following service naming conventions.

    This class is identical to ContainerApplication but follows the naming convention
    where long-running containerized applications are called "services".
    """
    pass
