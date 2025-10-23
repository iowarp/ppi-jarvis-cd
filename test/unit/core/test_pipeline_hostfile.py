"""
Test pipeline hostfile functionality.
"""
import pytest
import tempfile
import os
from pathlib import Path
from jarvis_cd.core.pipeline import Pipeline
from jarvis_cd.core.config import Jarvis
from jarvis_cd.util.hostfile import Hostfile


@pytest.fixture
def jarvis_env(tmp_path):
    """Setup Jarvis environment for testing"""
    # Create Jarvis directories
    config_dir = tmp_path / "config"
    private_dir = tmp_path / "private"
    shared_dir = tmp_path / "shared"

    config_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    shared_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Jarvis
    Jarvis._instance = None  # Reset singleton

    # Get Jarvis singleton and initialize it
    jarvis = Jarvis.get_instance()
    jarvis.initialize(str(config_dir), str(private_dir), str(shared_dir), force=True)

    yield jarvis, tmp_path

    # Cleanup
    Jarvis._instance = None


def test_pipeline_localhost_hostfile(jarvis_env):
    """Test pipeline with localhost hostfile"""
    jarvis, tmp_path = jarvis_env

    # Create a localhost hostfile
    hostfile_path = tmp_path / "localhost_hostfile"
    with open(hostfile_path, 'w') as f:
        f.write("localhost\n")

    # Create pipeline
    pipeline = Pipeline()
    pipeline.create("test_pipeline")

    # Set pipeline hostfile
    pipeline.hostfile = Hostfile(path=str(hostfile_path))
    pipeline.save()

    # Verify hostfile is set
    assert pipeline.hostfile is not None
    assert len(pipeline.hostfile.hosts) == 1
    assert pipeline.hostfile.hosts[0] == "localhost"

    # Load pipeline and verify hostfile persists
    pipeline2 = Pipeline("test_pipeline")
    assert pipeline2.hostfile is not None
    assert len(pipeline2.hostfile.hosts) == 1
    assert pipeline2.hostfile.hosts[0] == "localhost"

    # Test get_hostfile method
    effective_hostfile = pipeline2.get_hostfile()
    assert effective_hostfile is not None
    assert len(effective_hostfile.hosts) == 1
    assert effective_hostfile.hosts[0] == "localhost"


def test_pipeline_hostfile_fallback_to_jarvis(jarvis_env):
    """Test pipeline falls back to jarvis global hostfile"""
    jarvis, tmp_path = jarvis_env

    # Create pipeline without hostfile
    pipeline = Pipeline()
    pipeline.create("test_pipeline2")

    # Verify pipeline hostfile is None
    assert pipeline.hostfile is None

    # But get_hostfile() should return jarvis hostfile (defaults to localhost)
    effective_hostfile = pipeline.get_hostfile()
    assert effective_hostfile is not None
    assert len(effective_hostfile.hosts) >= 1  # At least localhost


def test_pipeline_hostfile_container_path(jarvis_env):
    """Test hostfile path is updated for containerized pipelines"""
    jarvis, tmp_path = jarvis_env

    # Create a hostfile
    hostfile_path = tmp_path / "test_hostfile"
    with open(hostfile_path, 'w') as f:
        f.write("localhost\n")

    # Create containerized pipeline
    pipeline = Pipeline()
    pipeline.create("test_container_pipeline")
    pipeline.container_name = "test_container"
    pipeline.hostfile = Hostfile(path=str(hostfile_path))
    pipeline.save()

    # Load pipeline config
    config_dir = jarvis.get_pipeline_dir("test_container_pipeline")
    config_file = config_dir / "pipeline.yaml"

    import yaml
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Verify hostfile path is set to container path
    assert config['hostfile'] == "/root/.ppi-jarvis/hostfile"


def test_package_hostfile_fallback(jarvis_env):
    """Test package hostfile falls back to pipeline hostfile"""
    jarvis, tmp_path = jarvis_env

    # Create pipeline with hostfile
    pipeline = Pipeline()
    pipeline.create("test_pkg_pipeline")

    hostfile_path = tmp_path / "pipeline_hostfile"
    with open(hostfile_path, 'w') as f:
        f.write("localhost\n")

    pipeline.hostfile = Hostfile(path=str(hostfile_path))
    pipeline.save()

    # Create a simple package class
    from jarvis_cd.core.pkg import Pkg

    class TestPkg(Pkg):
        pass

    # Create package instance
    pkg = TestPkg(pipeline)
    pkg.config = {}  # Empty config means no package-specific hostfile

    # Package should fall back to pipeline hostfile
    pkg_hostfile = pkg.get_hostfile()
    assert pkg_hostfile is not None
    assert len(pkg_hostfile.hosts) == 1
    assert pkg_hostfile.hosts[0] == "localhost"
