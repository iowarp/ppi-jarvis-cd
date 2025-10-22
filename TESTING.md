# Testing Guide

This document describes how to run tests for the ppi-jarvis-cd project.

## Running Tests Locally

### Prerequisites
- Python 3.8+
- pytest
- MPI implementation (OpenMPI, MPICH, or Intel MPI)

### Install Test Dependencies
```bash
pip install pytest pytest-cov pyyaml
```

### Run All Tests
```bash
pytest -xvs test/
```

### Run Specific Test Files
```bash
# Run only MPI tests
pytest -xvs test/unit/test_mpi_exec.py

# Run only argparse tests
pytest -xvs test/unit/test_argparse.py

# Run only hostfile tests
pytest -xvs test/unit/test_hostfile.py
```

### Run with Coverage
```bash
pytest --cov=jarvis_cd --cov-report=html test/
```

## Running Tests in Docker Container

The project provides a Docker container pre-configured with all necessary dependencies, including MPI via Spack.

### Build the Test Container
```bash
docker build -f Dockerfile.test -t jarvis-cd-test .
```

### Run All Tests in Container
```bash
docker run --rm jarvis-cd-test
```

### Run Specific Tests in Container
```bash
# Run only MPI tests
docker run --rm jarvis-cd-test pytest -xvs test/unit/test_mpi_exec.py

# Run with coverage
docker run --rm jarvis-cd-test pytest --cov=jarvis_cd --cov-report=term test/
```

### Interactive Container Session
```bash
# Start an interactive bash session
docker run --rm -it jarvis-cd-test /bin/bash

# Inside the container, MPI is already loaded via:
# source /opt/spack/share/spack/setup-env.sh && spack load mpi

# Run tests interactively
pytest -xvs test/

# Check MPI version
mpiexec --version
```

### Mount Local Code for Development
```bash
# Mount your local code to test changes without rebuilding
docker run --rm -v $(pwd):/app jarvis-cd-test pytest -xvs test/
```

## Test Structure

- `test/unit/` - Unit tests for individual components
  - `test_argparse.py` - Argument parsing tests
  - `test_hostfile.py` - Hostfile parsing and manipulation tests
  - `test_mpi_exec.py` - MPI execution factory tests

## Writing New Tests

### Unit Test Template
```python
import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.your.module import YourClass


class TestYourClass(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        pass

    def tearDown(self):
        """Clean up after tests"""
        pass

    def test_something(self):
        """Test description"""
        # Your test code
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
```

## CI/CD Integration

The test container can be integrated into CI/CD pipelines:

```yaml
# Example GitLab CI
test:
  image: iowarp/iowarp-deps:ai
  script:
    - source /opt/spack/share/spack/setup-env.sh
    - spack load mpi
    - pip install pytest pytest-cov pyyaml
    - pytest --cov=jarvis_cd test/
```

## Troubleshooting

### MPI Not Found
If you get "mpiexec not found" errors:
```bash
# Load MPI in the container
source /opt/spack/share/spack/setup-env.sh
spack load mpi
```

### Import Errors
Ensure the project root is in your Python path:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
```

### Permission Issues in Docker
If you encounter permission issues with mounted volumes:
```bash
docker run --rm --user $(id -u):$(id -g) -v $(pwd):/app jarvis-cd-test
```
