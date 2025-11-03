"""Post-installation script to install builtin packages."""
import os
import shutil
from pathlib import Path


def install_builtin_packages():
    """Install builtin packages to ~/.ppi-jarvis/builtin during pip install."""
    jarvis_root = Path.home() / '.ppi-jarvis'
    builtin_target = jarvis_root / 'builtin'

    # If builtin already exists, nothing to do
    if builtin_target.exists():
        print(f"Builtin packages already installed at {builtin_target}")
        return

    # Create jarvis root directory
    jarvis_root.mkdir(parents=True, exist_ok=True)

    # Find builtin source directory
    try:
        # Get the directory containing this file
        this_file = Path(__file__).resolve()
        project_root = this_file.parent.parent  # Go up from jarvis_cd/post_install.py to project root
        builtin_source = project_root / 'builtin'

        if builtin_source.exists():
            print(f"Installing Jarvis-CD builtin packages...")
            print(f"Source: {builtin_source}")
            print(f"Target: {builtin_target}")

            # Always copy
            shutil.copytree(builtin_source, builtin_target)
            print(f"Copied builtin packages to {builtin_target}")

            # Count packages
            builtin_pkgs = builtin_target / 'builtin'
            if builtin_pkgs.exists():
                packages = [d for d in builtin_pkgs.iterdir()
                           if d.is_dir() and d.name != '__pycache__']
                print(f"Successfully installed {len(packages)} builtin packages")
        else:
            print(f"Warning: Could not find builtin packages directory at {builtin_source}")

    except Exception as e:
        print(f"Warning: Could not install builtin packages: {e}")


if __name__ == '__main__':
    install_builtin_packages()
