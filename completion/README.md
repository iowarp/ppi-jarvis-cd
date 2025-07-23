# Jarvis Bash Completion

This directory contains bash completion support for the Jarvis CD command-line tool.

## Features

- **Command completion**: Complete main commands like `jarvis pipeline`, `jarvis pkg`, etc.
- **Subcommand completion**: Complete subcommands like `jarvis pipeline append`, `jarvis pkg help`, etc.
- **Dynamic package completion**: Complete package names based on available packages in repositories
- **Pipeline completion**: Complete pipeline names for commands that accept them
- **File completion**: Complete file paths for commands that expect files
- **Flag completion**: Complete common command-line flags

## Example Usage

```bash
# Command completion
jarvis pi<TAB>         # Completes to "pipeline"
jarvis pipeline ap<TAB> # Completes to "append"

# Package name completion
jarvis pipeline append la<TAB>    # Completes to "lammps"
jarvis pipeline append gr<TAB>    # Shows "gray_scott"
jarvis pkg help wr<TAB>           # Completes to "wrf"

# Show all available packages starting with 'h'
jarvis pipeline append h<TAB><TAB>
# Shows: hermes_api, hermes_api_bench, hermes_mpiio_tests, etc.
```

## Installation

### Automatic Installation (Recommended)

Run the installation script from the project root:

```bash
./install-completion.sh
```

This will:
1. Install the completion script to the appropriate system or user directory
2. Check if bash-completion is properly configured
3. Verify that the jarvis command and helper scripts are accessible

### Manual Installation

1. **System-wide installation** (requires root):
   ```bash
   sudo cp completion/jarvis-completion.bash /usr/share/bash-completion/completions/jarvis
   ```

2. **User-specific installation**:
   ```bash
   mkdir -p ~/.local/share/bash-completion/completions
   cp completion/jarvis-completion.bash ~/.local/share/bash-completion/completions/jarvis
   ```

3. **Direct sourcing** (temporary):
   ```bash
   source completion/jarvis-completion.bash
   ```

### Prerequisites

- **bash-completion**: Most Linux distributions have this installed by default
- **jarvis command**: Must be installed and available in PATH
- **jarvis-completion-helper**: Installed automatically with jarvis

## How It Works

The completion system consists of two parts:

1. **jarvis-completion.bash**: The main bash completion script that handles command parsing and completion logic
2. **jarvis-completion-helper**: A Python script that dynamically discovers available packages and pipelines

The completion script intelligently determines what type of completion is needed based on the current command context and calls the helper script to get dynamic data like package names.

## Troubleshooting

### Completion Not Working

1. **Restart your shell** or run `source ~/.bashrc`
2. **Check if bash-completion is enabled**:
   ```bash
   # Add to ~/.bashrc if not present
   if [[ -f /usr/share/bash-completion/bash_completion ]]; then
       . /usr/share/bash-completion/bash_completion
   fi
   ```
3. **Verify jarvis is in PATH**:
   ```bash
   which jarvis  # Should show the jarvis executable path
   ```
4. **Check helper script**:
   ```bash
   jarvis-completion-helper packages  # Should list available packages
   ```

### Package Names Not Completing

- Ensure jarvis is properly installed: `pip install .`
- Check that package discovery is working: `jarvis-completion-helper packages`
- Verify repository configuration: `jarvis repo list`

### Adding Custom Packages

The completion system automatically discovers packages from all configured repositories. To add custom packages:

1. Add your repository: `jarvis repo add /path/to/your/repo`
2. Restart your shell to refresh completion cache
3. Your packages should now appear in completion

## Supported Commands

The completion system supports the following command patterns:

- `jarvis pipeline append <package_name>`
- `jarvis pipeline prepend <package_name>`
- `jarvis pipeline insert <position> <package_name>`
- `jarvis pkg help <package_name>`
- `jarvis pkg readme <package_name>`
- `jarvis pkg src <package_name>`
- `jarvis pkg root <package_name>`
- `jarvis pkg configure <pipeline_id>`
- File and path arguments for applicable commands
- Common command-line flags and options