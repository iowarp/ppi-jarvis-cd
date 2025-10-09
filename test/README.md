# Jarvis CD Test Suite

Comprehensive unit tests for the Jarvis CD project, organized into three main categories:
- **core**: Tests for CLI commands and core functionality
- **shell**: Tests for execution modules (LocalExec, SshExec, etc.)
- **util**: Tests for utility modules (argparse, hostfile, etc.)

## Test Structure

```
test/
├── unit/
│   ├── core/          # CLI command tests
│   │   ├── test_cli_base.py
│   │   ├── test_cli_init.py
│   │   ├── test_cli_pipeline.py
│   │   ├── test_cli_repo_pkg.py
│   │   └── test_cli_env_rg.py
│   ├── shell/         # Execution module tests
│   │   ├── test_local_exec.py
│   │   ├── test_ssh_exec.py
│   │   ├── test_scp_exec.py
│   │   ├── test_mpi_exec.py
│   │   └── test_env_forwarding.py
│   └── util/          # Utility module tests
│       ├── test_argparse.py
│       ├── test_argparse_comprehensive.py
│       └── test_hostfile.py
├── Dockerfile         # Docker container for isolated testing
├── docker-compose.yml # Docker Compose configuration
├── run_tests.sh       # Test runner script
└── README.md          # This file
```

## Running Tests

### Option 1: Using Docker (Recommended)

Docker provides an isolated environment that won't affect your host system.

**Run all tests:**
```bash
./test/run_tests.sh all
```

**Run specific test suites:**
```bash
./test/run_tests.sh shell    # Shell module tests only
./test/run_tests.sh util     # Utility module tests only
./test/run_tests.sh core     # Core CLI tests only
./test/run_tests.sh parallel # All tests in parallel
```

**Pass additional pytest arguments:**
```bash
./test/run_tests.sh all -v --tb=short
./test/run_tests.sh shell -k test_local
./test/run_tests.sh parallel -n 4
```

### Option 2: Using Docker Compose Directly

```bash
cd test/

# Run all tests
docker-compose run --rm test

# Run specific test suite
docker-compose run --rm test-shell
docker-compose run --rm test-util
docker-compose run --rm test-core

# Run tests in parallel
docker-compose run --rm test-parallel
```

### Option 3: Local Python Environment

If you prefer to run tests locally (not containerized):

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-xdist

# Run all tests
python -m pytest test/unit/ -v

# Run specific test directory
python -m pytest test/unit/shell/ -v
python -m pytest test/unit/util/ -v
python -m pytest test/unit/core/ -v

# Run with coverage
python -m pytest test/unit/ --cov=jarvis_cd --cov-report=term-missing --cov-report=html

# Run tests in parallel
python -m pytest test/unit/ -n auto
```

## Test Categories

### Core Tests (test/unit/core/)

Tests for CLI commands and core functionality:

- **test_cli_init.py**: `jarvis init` command
- **test_cli_pipeline.py**: `jarvis ppl` commands (create, append, run, start, stop, etc.)
- **test_cli_repo_pkg.py**: `jarvis repo` and `jarvis pkg` commands
- **test_cli_env_rg.py**: Environment, resource graph, module, and hostfile commands

**Key Features Tested:**
- Command parsing and argument validation
- Default values and required arguments
- Command aliases
- Error handling

### Shell Tests (test/unit/shell/)

Tests for execution modules:

- **test_local_exec.py**: LocalExec execution and environment handling
- **test_ssh_exec.py**: SSH/PSSH remote execution
- **test_scp_exec.py**: SCP/PSCP file transfer
- **test_mpi_exec.py**: MPI parallel execution
- **test_env_forwarding.py**: Environment variable forwarding across all exec types

**Key Features Tested:**
- Environment variable forwarding and type conversion
- Command construction and escaping
- Output collection and piping
- Async execution
- Error handling and exit codes

### Util Tests (test/unit/util/)

Tests for utility modules:

- **test_argparse.py**: Basic argument parsing
- **test_argparse_comprehensive.py**: Comprehensive argparse testing
- **test_hostfile.py**: Hostfile parsing and management

**Key Features Tested:**
- Type conversions (int, float, str, bool, list, dict)
- Required arguments and defaults
- Positional and keyword arguments
- Boolean flags (+/-)
- Choices validation
- Remainder arguments

## Code Coverage

After running tests with coverage, view the HTML report:

```bash
# Coverage report is generated in htmlcov/
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Current Coverage Targets:**
- Shell modules: 70-100% coverage
- Util modules: 70-90% coverage
- Core modules: Initial coverage being established

## Writing New Tests

### Adding CLI Command Tests

1. Create a new test file in `test/unit/core/`
2. Inherit from `CLITestBase` for common utilities
3. Use helper methods like `run_command()`, `create_test_pipeline()`, etc.

Example:
```python
from test_cli_base import CLITestBase

class TestMyCLICommand(CLITestBase):
    def test_my_command(self):
        args = ['my', 'command', 'arg1']
        result = self.run_command(args)
        self.assertTrue(result.get('success'))
        self.assertEqual(result['kwargs']['arg_name'], 'arg1')
```

### Adding Shell Tests

1. Create tests in `test/unit/shell/`
2. Test execution, environment variables, and output handling
3. Use cross-platform Python scripts for verification

### Adding Util Tests

1. Create tests in `test/unit/util/`
2. Focus on API correctness and type conversions
3. Test edge cases and error conditions

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests in Docker
  run: ./test/run_tests.sh all

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./htmlcov/coverage.xml
```

## Troubleshooting

### Docker Issues

**Problem**: Docker build fails
```bash
# Clean Docker cache and rebuild
docker system prune -a
cd test && docker-compose build --no-cache
```

**Problem**: Permission denied
```bash
# Ensure run_tests.sh is executable
chmod +x test/run_tests.sh
```

### Test Failures

**Problem**: SSH/SCP tests fail
- Expected behavior: Some tests use mock hostnames that won't resolve
- These failures are normal in isolated environments

**Problem**: MPI tests skipped
- Expected behavior: MPI tests skip when OpenMPI is not installed
- Use Docker environment for full MPI test coverage

### Coverage Issues

**Problem**: Coverage report not generated
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Generate coverage explicitly
python -m pytest test/unit/ --cov=jarvis_cd --cov-report=html
```

## Best Practices

1. **Isolation**: Tests should not depend on external state
2. **Cleanup**: Use setUp/tearDown to manage test resources
3. **Assertions**: Be specific with assertions (assertEqual vs assertTrue)
4. **Documentation**: Add docstrings to test methods
5. **Naming**: Use descriptive test names (test_feature_scenario)

## Contributing

When adding new features to Jarvis CD:

1. Write tests first (TDD approach recommended)
2. Ensure tests pass locally
3. Run full test suite in Docker before submitting PR
4. Aim for 80%+ coverage on new code
5. Update this README if adding new test categories

## Support

For questions or issues with the test suite:
- Check existing tests for examples
- Review pytest documentation: https://docs.pytest.org/
- Open an issue in the project repository
