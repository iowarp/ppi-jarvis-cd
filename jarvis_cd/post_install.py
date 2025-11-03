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
        import jarvis_cd
        jarvis_cd_path = Path(jarvis_cd.__file__).parent

        # Try multiple locations
        possible_sources = [
            jarvis_cd_path.parent / 'builtin',  # Installed alongside jarvis_cd
            jarvis_cd_path.parent.parent / 'builtin',  # Development mode
        ]

        builtin_source = None
        for source in possible_sources:
            if source.exists() and (source / 'builtin').exists():
                builtin_source = source
                break

        if builtin_source:
            print(f"Installing Jarvis-CD builtin packages...")
            print(f"Source: {builtin_source}")
            print(f"Target: {builtin_target}")

            # In development mode (if we can write to source), create symlink
            # Otherwise copy
            try:
                if os.access(builtin_source, os.W_OK):
                    # Development mode - create symlink
                    builtin_target.symlink_to(builtin_source.absolute())
                    print(f"Created symlink (dev mode): {builtin_target} -> {builtin_source}")
                else:
                    # Production mode - copy
                    shutil.copytree(builtin_source, builtin_target)
                    print(f"Copied builtin packages to {builtin_target}")

                # Count packages
                builtin_pkgs = builtin_target / 'builtin'
                if builtin_pkgs.exists():
                    packages = [d for d in builtin_pkgs.iterdir()
                               if d.is_dir() and d.name != '__pycache__']
                    print(f"Successfully installed {len(packages)} builtin packages")
            except OSError:
                # Symlink failed, try copy
                if builtin_target.is_symlink():
                    builtin_target.unlink()
                shutil.copytree(builtin_source, builtin_target)
                print(f"Copied builtin packages to {builtin_target}")
        else:
            print(f"Warning: Could not find builtin packages directory")
            print(f"Searched: {', '.join(str(p) for p in possible_sources)}")

    except Exception as e:
        print(f"Warning: Could not install builtin packages: {e}")


if __name__ == '__main__':
    install_builtin_packages()
