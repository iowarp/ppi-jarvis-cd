"""
Container image management for Jarvis-CD.
Handles listing and removing container images.
"""

import yaml
from pathlib import Path
from jarvis_cd.core.config import Jarvis


class ContainerManager:
    """
    Manages container images for Jarvis-CD.
    Provides methods to list and remove container images.
    """

    def __init__(self):
        """Initialize ContainerManager"""
        self.jarvis = Jarvis.get_instance()
        self.containers_dir = Path.home() / '.ppi-jarvis' / 'containers'
        self.containers_dir.mkdir(parents=True, exist_ok=True)

    def list_containers(self):
        """
        List all container images.
        Shows container name, number of packages, and status.
        """
        if not self.containers_dir.exists():
            print("No containers found")
            return

        # Find all .yaml manifest files
        manifest_files = list(self.containers_dir.glob('*.yaml'))

        if not manifest_files:
            print("No containers found")
            return

        print("Container images:")
        for manifest_file in sorted(manifest_files):
            container_name = manifest_file.stem

            # Load manifest to count packages
            try:
                with open(manifest_file, 'r') as f:
                    manifest = yaml.safe_load(f) or {}
                num_packages = len(manifest)
            except:
                num_packages = 0

            # Check if Dockerfile exists
            dockerfile_path = self.containers_dir / f"{container_name}.Dockerfile"
            has_dockerfile = dockerfile_path.exists()

            status = "✓" if has_dockerfile else "✗"
            print(f"  {status} {container_name} ({num_packages} packages)")

    def remove_container(self, container_name: str):
        """
        Remove a container image and its files.
        Removes Dockerfile, manifest, and container image.

        :param container_name: Name of container to remove
        """
        # Remove Dockerfile
        dockerfile_path = self.containers_dir / f"{container_name}.Dockerfile"
        if dockerfile_path.exists():
            dockerfile_path.unlink()
            print(f"Removed Dockerfile: {dockerfile_path}")

        # Remove manifest
        manifest_path = self.containers_dir / f"{container_name}.yaml"
        if manifest_path.exists():
            manifest_path.unlink()
            print(f"Removed manifest: {manifest_path}")

        # Remove container image using container engine
        from jarvis_cd.shell import Exec, LocalExecInfo

        # Try podman first, then docker
        for engine in ['podman', 'docker']:
            try:
                remove_cmd = f"{engine} rmi {container_name}"
                print(f"Removing container image with: {remove_cmd}")
                Exec(remove_cmd, LocalExecInfo()).run()
                print(f"Container image removed: {container_name}")
                break
            except:
                # Try next engine
                continue

        print(f"Container '{container_name}' removed")
