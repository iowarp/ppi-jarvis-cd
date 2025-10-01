# Jarvis-CD Module Management

The `jarvis mod` system provides a complete solution for creating and managing modulefiles for manually-installed packages. This system generates both YAML and TCL modulefiles that can be used for environment management and integration with module systems like Environment Modules.

## Table of Contents

1. [Overview](#overview)
2. [Basic Usage Workflow](#basic-usage-workflow)
3. [Module Directory Structure](#module-directory-structure)
4. [CLI Commands Reference](#cli-commands-reference)
5. [Modulefile Formats](#modulefile-formats)
6. [Environment Profile Building](#environment-profile-building)
7. [Advanced Usage](#advanced-usage)
8. [Integration with Package Managers](#integration-with-package-managers)

## Overview

The Jarvis module system allows you to:

- **Create isolated package environments** with dedicated directory structures
- **Generate TCL modulefiles** compatible with Environment Modules
- **Generate YAML configuration files** for easy scripting and automation
- **Manage environment variables** (PATH, LD_LIBRARY_PATH, etc.) systematically
- **Build environment profiles** in multiple formats for IDE and build system integration
- **Track package dependencies** between modules

### Key Features

- **Automatic TCL generation**: YAML configurations are automatically converted to TCL modulefiles
- **Environment variable management**: Support for both prepend and set operations
- **Dependency tracking**: Module dependencies are tracked and included in TCL files
- **Current module context**: Work with a "current" module to avoid repetitive typing
- **Profile building**: Export current environment for IDEs and build systems

## Basic Usage Workflow

Here's a complete example of manually installing zlib using the jarvis module system:

```bash
# 1. Create a new module
jarvis mod create zlib

# 2. Navigate to source directory and download/build
cd $(jarvis mod src zlib)
wget https://www.zlib.net/zlib-1.3.tar.gz
tar -xzf zlib-1.3.tar.gz
cd zlib-1.3

# 3. Configure with module installation prefix
./configure --prefix=$(jarvis mod root zlib)

# 4. Build and install
make -j8 install

# 5. Configure module environment variables
jarvis mod prepend zlib PATH="$(jarvis mod root zlib)/bin"
jarvis mod prepend zlib LD_LIBRARY_PATH="$(jarvis mod root zlib)/lib"
jarvis mod prepend zlib PKG_CONFIG_PATH="$(jarvis mod root zlib)/lib/pkgconfig"

# 6. Set package-specific environment variables
jarvis mod setenv zlib ZLIB_ROOT="$(jarvis mod root zlib)"
jarvis mod setenv zlib ZLIB_VERSION="1.3"
```

After this workflow, you'll have:
- Package installed in `~/.ppi-jarvis-mods/packages/zlib/`
- YAML configuration at `~/.ppi-jarvis-mods/modules/zlib.yaml`
- TCL modulefile at `~/.ppi-jarvis-mods/modules/zlib`

## Module Directory Structure

The jarvis module system creates a well-organized directory structure:

```
~/.ppi-jarvis-mods/
├── packages/                    # Package installation directories
│   ├── zlib/                   # Example package directory
│   │   ├── bin/               # Installed binaries
│   │   ├── lib/               # Installed libraries
│   │   ├── include/           # Header files
│   │   └── src/               # Source code directory
│   └── openssl/
│       ├── bin/
│       ├── lib/
│       ├── include/
│       └── src/
└── modules/                    # Module configuration files
    ├── zlib.yaml              # YAML configuration
    ├── zlib                   # TCL modulefile
    ├── openssl.yaml
    └── openssl
```

### Directory Purposes

- **`packages/`**: Root directory for all package installations
- **`packages/{module}/`**: Installation prefix for each package (`$(jarvis mod root {module})`)
- **`packages/{module}/src/`**: Source code working directory (`$(jarvis mod src {module})`)
- **`modules/`**: Configuration and modulefile storage
- **`modules/{module}.yaml`**: YAML configuration file (`$(jarvis mod yaml {module})`)
- **`modules/{module}`**: TCL modulefile (`$(jarvis mod tcl {module})`)

## CLI Commands Reference

### Module Creation and Management

#### `jarvis mod create [mod_name]`
Create a new module with directory structure and configuration files.

```bash
# Create module with specific name
jarvis mod create mypackage

# Create module with generated name (if no name provided)
jarvis mod create
# Output: No module name provided, using: module_1640995200
```

**Creates:**
- Package directory: `~/.ppi-jarvis-mods/packages/{mod_name}/`
- Source directory: `~/.ppi-jarvis-mods/packages/{mod_name}/src/`
- YAML configuration: `~/.ppi-jarvis-mods/modules/{mod_name}.yaml`
- TCL modulefile: `~/.ppi-jarvis-mods/modules/{mod_name}`
- Sets the new module as current

#### `jarvis mod cd <mod_name>`
Set the current active module for subsequent operations.

```bash
jarvis mod cd zlib
# Set current module: zlib

# Now you can omit module name in other commands
jarvis mod root        # Uses current module (zlib)
jarvis mod prepend PATH="/opt/zlib/bin"  # Modifies current module
```

#### `jarvis mod list`
List all available modules with current module indicator.

```bash
jarvis mod list
# Available modules:
#   openssl
# * zlib        # * indicates current module
```

#### `jarvis mod destroy [mod_name]`
Completely remove a module and all its files.

```bash
# Destroy specific module
jarvis mod destroy old_package

# Destroy current module
jarvis mod destroy
```

**Removes:**
- Package directory and all contents
- YAML configuration and TCL modulefile
- Clears current module if it was the destroyed one

#### `jarvis mod clear [mod_name]`
Clear the module package directory, preserving only the `src/` directory. Useful for cleaning build artifacts while keeping source code.

```bash
# Clear specific module
jarvis mod clear mypackage

# Clear current module
jarvis mod cd mypackage
jarvis mod clear
```

**Removes:**
- All directories except `src/` (e.g., `bin/`, `lib/`, `include/`, `build/`)
- All files in the package root (e.g., `README.md`, build artifacts)

**Preserves:**
- The `src/` directory and all its contents

**Use case:** After building a package from source, you may want to clean up intermediate build files while keeping the original source code for rebuilding or reference.

### Environment Variable Management

#### `jarvis mod prepend [mod_name] ENV=VAL1;VAL2;VAL3 ...`
Prepend values to environment variables (typically for PATH-like variables).

```bash
# Prepend to specific module
jarvis mod prepend zlib PATH="/opt/zlib/bin" LD_LIBRARY_PATH="/opt/zlib/lib"

# Prepend to current module
jarvis mod prepend PKG_CONFIG_PATH="/opt/zlib/lib/pkgconfig"

# Multiple values using semicolon separator
jarvis mod prepend zlib PATH="/opt/zlib/bin;/opt/zlib/sbin"
```

#### `jarvis mod setenv [mod_name] ENV=VAL ...`
Set environment variables to specific values.

```bash
# Set variables for specific module
jarvis mod setenv zlib ZLIB_ROOT="/opt/zlib" ZLIB_VERSION="1.3"

# Set variables for current module
jarvis mod setenv CC="gcc-9" CXX="g++-9"
```

### Directory Path Commands

#### `jarvis mod root [mod_name]`
Print the root installation directory for a module.

```bash
jarvis mod root zlib
# /home/user/.ppi-jarvis-mods/packages/zlib

# Use in shell commands
cd $(jarvis mod root zlib)
./configure --prefix=$(jarvis mod root zlib)
```

#### `jarvis mod src [mod_name]`
Print the source directory for a module.

```bash
jarvis mod src zlib
# /home/user/.ppi-jarvis-mods/packages/zlib/src

# Use in shell commands
cd $(jarvis mod src zlib)
wget https://example.com/source.tar.gz
```

#### `jarvis mod tcl [mod_name]`
Print the path to the TCL modulefile.

```bash
jarvis mod tcl zlib
# /home/user/.ppi-jarvis-mods/modules/zlib

# Use with module command
module load $(jarvis mod tcl zlib)
```

#### `jarvis mod yaml [mod_name]`
Print the path to the YAML configuration file.

```bash
jarvis mod yaml zlib
# /home/user/.ppi-jarvis-mods/modules/zlib.yaml

# View configuration
cat $(jarvis mod yaml zlib)
```

#### `jarvis mod dir`
Print the global modules directory containing all YAML and TCL modulefiles.

```bash
jarvis mod dir
# /home/user/.ppi-jarvis-mods/modules

# Use to navigate to modules directory
cd $(jarvis mod dir)

# List all modulefiles
ls $(jarvis mod dir)
```

#### `jarvis mod profile [m=method] [path=file]`
Build a snapshot of current environment variables in various formats (same as environment profile building section).

#### `jarvis mod import <mod_name> <command>`
Create a module by automatically detecting environment changes before/after running a command.

```bash
# Import a module from a setup script
jarvis mod import mypackage "source /opt/mypackage/setup.sh"

# Import from an export command
jarvis mod import testlib "export PATH=/opt/testlib/bin:\$PATH"

# Import from a more complex command
jarvis mod import compiler "module load gcc/9.3.0 && export CC=gcc CXX=g++"
```

**Features:**
- Automatically detects changes in PATH-like environment variables
- Stores the command in the YAML file for later updates
- Creates both YAML and TCL modulefiles
- Tracks changes in: PATH, LD_LIBRARY_PATH, LIBRARY_PATH, INCLUDE, CPATH, PKG_CONFIG_PATH, CMAKE_PREFIX_PATH, JAVA_HOME, PYTHONPATH, CFLAGS, LDFLAGS

#### `jarvis mod update [mod_name]`
Update a module by re-running its stored command.

```bash
# Update specific module
jarvis mod update mypackage

# Update current module
jarvis mod cd mypackage
jarvis mod update
```

**Use cases:**
- Refresh module after environment changes
- Update module after software reinstallation
- Synchronize module with updated setup scripts

### Environment Profile Building

#### `jarvis mod profile [m=method] [path=file]`
Build a snapshot of current environment variables in various formats.

```bash
# Print to stdout in default format (dotenv)
jarvis mod profile

# Print in VSCode launch.json format
jarvis mod profile m=vscode

# Print in CLion environment format
jarvis mod profile m=clion

# Save to file in dotenv format
jarvis mod profile path=.env

# Save to file in CMake format
jarvis mod profile m=cmake path=env.cmake
```

#### `jarvis mod build profile [m=method] [path=file]`
Alternative command for building environment profiles (same functionality as `mod profile`).

```bash
# Print to stdout in default format (dotenv)
jarvis mod build profile

# Print in VSCode launch.json format
jarvis mod build profile m=vscode

# Print in CLion environment format
jarvis mod build profile m=clion

# Save to file in dotenv format
jarvis mod build profile path=.env

# Save to file in CMake format
jarvis mod build profile m=cmake path=env.cmake
```

**Supported formats:**
- **`dotenv`**: Standard .env file format (`VAR="value"`)
- **`cmake`**: CMake set commands (`set(ENV{VAR} "value")`)
- **`vscode`**: VSCode launch.json environment block
- **`clion`**: CLion environment configuration

## Modulefile Formats

### YAML Configuration Format

The YAML file contains structured configuration that's easy to read and modify:

```yaml
command: source /opt/mypackage/setup.sh  # Stored command for updates (optional)
deps:
  ppi-jarvis-util: true         # Module dependencies
doc:
  Name: zlib                    # Package documentation
  Version: "1.3"
  doc: "Compression library"
prepends:                       # Variables to prepend to
  CFLAGS: []
  CMAKE_PREFIX_PATH: []
  CPATH: []
  INCLUDE: []
  LDFLAGS: []
  LD_LIBRARY_PATH:
  - /home/user/.ppi-jarvis-mods/packages/zlib/lib
  LIBRARY_PATH: []
  PATH:
  - /home/user/.ppi-jarvis-mods/packages/zlib/bin
  PKG_CONFIG_PATH:
  - /home/user/.ppi-jarvis-mods/packages/zlib/lib/pkgconfig
  PYTHONPATH: []
setenvs:                        # Variables to set
  ZLIB_ROOT: /home/user/.ppi-jarvis-mods/packages/zlib
  ZLIB_VERSION: "1.3"
```

#### Command Storage
When modules are created using `jarvis mod import`, the original command is stored in the `command` field. This allows for:
- **Reproducible updates**: `jarvis mod update` can re-run the exact same command
- **Documentation**: The command serves as documentation for how the environment was set up
- **Version control**: Commands can be tracked and modified as needed

### TCL Modulefile Format

The TCL file is automatically generated from the YAML configuration:

```tcl
#%Module1.0
module-whatis 'Name: zlib'
module-whatis 'Version: 1.3'
module-whatis 'doc: Compression library'
module load ppi-jarvis-util
prepend-path LD_LIBRARY_PATH /home/user/.ppi-jarvis-mods/packages/zlib/lib
prepend-path PATH /home/user/.ppi-jarvis-mods/packages/zlib/bin
prepend-path PKG_CONFIG_PATH /home/user/.ppi-jarvis-mods/packages/zlib/lib/pkgconfig
setenv ZLIB_ROOT /home/user/.ppi-jarvis-mods/packages/zlib
setenv ZLIB_VERSION 1.3
```

### Module Dependencies

Dependencies between modules are tracked in the `deps` section:

```yaml
deps:
  base-compilers: true    # This module depends on base-compilers
  mpi-runtime: true       # This module depends on mpi-runtime
  optional-package: false # This dependency is disabled
```

Dependencies marked as `true` will generate `module load` statements in the TCL file.

## Environment Profile Building

The profile building feature captures important environment variables and exports them in various formats for IDE and build system integration.

### Captured Variables

The system captures these common environment variables:
- **PATH**: Executable search paths
- **LD_LIBRARY_PATH**: Dynamic library search paths
- **LIBRARY_PATH**: Static library search paths
- **INCLUDE, CPATH**: Header file search paths
- **PKG_CONFIG_PATH**: pkg-config search paths
- **CMAKE_PREFIX_PATH**: CMake package search paths
- **JAVA_HOME**: Java installation path
- **PYTHONPATH**: Python module search paths

### Output Formats

#### .env Format (dotenv)
```bash
PATH="/usr/local/bin:/usr/bin:/bin"
LD_LIBRARY_PATH="/usr/local/lib:/usr/lib"
CMAKE_PREFIX_PATH="/usr/local"
```

#### CMake Format
```cmake
set(ENV{PATH} "/usr/local/bin:/usr/bin:/bin")
set(ENV{LD_LIBRARY_PATH} "/usr/local/lib:/usr/lib")
set(ENV{CMAKE_PREFIX_PATH} "/usr/local")
```

#### VSCode Format
```json
"environment": {
  "PATH": "/usr/local/bin:/usr/bin:/bin",
  "LD_LIBRARY_PATH": "/usr/local/lib:/usr/lib",
  "CMAKE_PREFIX_PATH": "/usr/local"
}
```

#### CLion Format
```
PATH=/usr/local/bin:/usr/bin:/bin;LD_LIBRARY_PATH=/usr/local/lib:/usr/lib;CMAKE_PREFIX_PATH=/usr/local
```

## Advanced Usage

### Automatic Module Import Workflow

Use `jarvis mod import` for software that provides setup scripts:

```bash
# Import a module from Spack
jarvis mod import "spack-gcc" "spack load gcc@11.2.0"

# Import from Environment Modules
jarvis mod import "intel-compiler" "module load intel/2021.4"

# Import from custom setup script
jarvis mod import "mylib" "source /opt/mylib/env-setup.sh"

# Import from multiple commands
jarvis mod import "dev-env" "export CC=gcc && export CXX=g++ && export PATH=/opt/tools:\$PATH"

# Update modules when software is updated
jarvis mod update spack-gcc
```

### Working with Dependencies

Create modules that depend on other modules:

```bash
# Create base module
jarvis mod create base-tools
jarvis mod prepend base-tools PATH="/opt/base/bin"

# Create dependent module
jarvis mod create advanced-tools
jarvis mod prepend advanced-tools PATH="/opt/advanced/bin"

# Add dependency using the dep command
jarvis mod dep add base-tools advanced-tools

# Or add to current module
jarvis mod cd advanced-tools
jarvis mod dep add base-tools
```

The generated TCL file will include:
```tcl
module load base-tools
prepend-path PATH /opt/advanced/bin
```

#### Dependency Management Commands

**Add a dependency:**
```bash
jarvis mod dep add <dependency> [module_name]
```
Adds `dependency` as a requirement for `module_name`. If `module_name` is omitted, uses the current module.

**Remove a dependency:**
```bash
jarvis mod dep remove <dependency> [module_name]
```
Removes `dependency` from `module_name`. If `module_name` is omitted, uses the current module.

**Example:**
```bash
# Add multiple dependencies to a module
jarvis mod cd myapp
jarvis mod dep add zlib
jarvis mod dep add openssl
jarvis mod dep add python

# Remove a dependency
jarvis mod dep remove python

# Work with a specific module
jarvis mod dep add gcc myapp
jarvis mod dep remove gcc myapp
```

### Batch Environment Setup

Set up multiple environment variables at once:

```bash
# Configure compiler environment
jarvis mod create gcc-toolchain
jarvis mod setenv gcc-toolchain \
  CC="gcc-9" \
  CXX="g++-9" \
  FC="gfortran-9" \
  CFLAGS="-O3 -march=native" \
  CXXFLAGS="-O3 -march=native"

jarvis mod prepend gcc-toolchain \
  PATH="/opt/gcc-9/bin" \
  LD_LIBRARY_PATH="/opt/gcc-9/lib64" \
  LIBRARY_PATH="/opt/gcc-9/lib64" \
  CMAKE_PREFIX_PATH="/opt/gcc-9"
```

### Integration with Build Systems

#### CMake Integration
```bash
# Build environment profile for CMake
jarvis mod profile m=cmake path=build-env.cmake

# Use in CMakeLists.txt
include(build-env.cmake)
```

#### IDE Integration
```bash
# Generate VSCode environment
jarvis mod profile m=vscode

# Copy output to .vscode/launch.json environment section
```

### Module Templating

Create reusable module templates by copying YAML files:

```bash
# Create template module
jarvis mod create template-package

# Copy and customize
cp $(jarvis mod yaml template-package) $(jarvis mod yaml new-package)
# Edit new-package.yaml as needed

# Regenerate TCL file
jarvis mod setenv new-package DUMMY="trigger_regeneration"
```

## Integration with Package Managers

The jarvis module system integrates well with other package management approaches:

### With Spack
```bash
# Install with Spack, then create module
spack install zlib
jarvis mod create zlib-spack
jarvis mod prepend zlib-spack PATH="$(spack location -i zlib)/bin"
jarvis mod prepend zlib-spack LD_LIBRARY_PATH="$(spack location -i zlib)/lib"
```

### With Conda/Mamba
```bash
# Install with conda, then create module
conda create -n myenv package_name
jarvis mod create conda-myenv
jarvis mod prepend conda-myenv PATH="$CONDA_PREFIX/bin"
jarvis mod setenv conda-myenv CONDA_ENV_NAME="myenv"
```

### With Manual Installation
The primary use case - installing packages manually:

```bash
jarvis mod create custom-package
cd $(jarvis mod src custom-package)

# Download and build
git clone https://github.com/project/repo.git
cd repo
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$(jarvis mod root custom-package) ..
make -j8 install

# Configure module
jarvis mod prepend custom-package PATH="$(jarvis mod root custom-package)/bin"
jarvis mod prepend custom-package LD_LIBRARY_PATH="$(jarvis mod root custom-package)/lib"
```

## Best Practices

### Naming Conventions
- Use descriptive module names: `gcc-toolchain`, `openmpi-4.1`, `custom-analysis-tools`
- Include version numbers when managing multiple versions: `zlib-1.3`, `openssl-3.0`
- Use hyphens rather than underscores for consistency

### Directory Organization
- Keep source code in the `src/` directory for easy reference
- Use consistent installation prefixes via `$(jarvis mod root module)`
- Document installation procedures in README files within source directories

### Environment Management
- Prepend to PATH-like variables rather than setting them completely
- Set package-specific variables (like `ZLIB_ROOT`) using `setenv`
- Use dependency tracking for complex package relationships

### Profile Building
- Create environment profiles before starting development sessions
- Use appropriate formats for different tools (VSCode, CLion, CMake)
- Keep profiles up to date as your environment changes

This comprehensive module management system provides a complete solution for managing manually-installed packages with automatic modulefile generation and flexible environment configuration.