import setuptools

# Use setup() with minimal configuration since pyproject.toml handles most metadata
setuptools.setup(
    scripts=['bin/jarvis'],
)

# Install builtin packages immediately after setup
try:
    from jarvis_cd.post_install import install_builtin_packages
    install_builtin_packages()
except Exception as e:
    print(f"Warning: Could not install builtin packages: {e}")
