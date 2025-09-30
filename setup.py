import setuptools

# Use setup() with minimal configuration since pyproject.toml handles most metadata
# Builtin packages are now installed automatically on first `jarvis` command run
setuptools.setup(
    scripts=['bin/jarvis'],
)
