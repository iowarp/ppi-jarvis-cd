#!/bin/bash
# Installation script for Jarvis bash completion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPLETION_DIR="$SCRIPT_DIR/completion"
BIN_DIR="$SCRIPT_DIR/bin"

# Check if completion files exist
if [[ ! -f "$COMPLETION_DIR/jarvis-completion.bash" ]]; then
    print_error "Completion script not found at $COMPLETION_DIR/jarvis-completion.bash"
    exit 1
fi

if [[ ! -f "$BIN_DIR/jarvis-completion-helper" ]]; then
    print_error "Completion helper not found at $BIN_DIR/jarvis-completion-helper"
    exit 1
fi

print_status "Installing Jarvis bash completion..."

# Determine completion directory
if [[ -d "/usr/share/bash-completion/completions" ]]; then
    SYSTEM_COMPLETION_DIR="/usr/share/bash-completion/completions"
elif [[ -d "/etc/bash_completion.d" ]]; then
    SYSTEM_COMPLETION_DIR="/etc/bash_completion.d"
else
    SYSTEM_COMPLETION_DIR=""
fi

# Check if we can install system-wide
if [[ -n "$SYSTEM_COMPLETION_DIR" ]] && [[ -w "$SYSTEM_COMPLETION_DIR" ]]; then
    print_status "Installing system-wide completion to $SYSTEM_COMPLETION_DIR"
    cp "$COMPLETION_DIR/jarvis-completion.bash" "$SYSTEM_COMPLETION_DIR/jarvis"
    print_status "System-wide installation complete!"
    print_status "Bash completion will be available in new shell sessions."
elif [[ "$EUID" -eq 0 ]]; then
    # Running as root but system directories don't exist or aren't writable
    print_error "System completion directories not found or not writable"
    exit 1
else
    # Install user-specific completion
    USER_COMPLETION_DIR="$HOME/.local/share/bash-completion/completions"
    
    print_status "Installing user-specific completion to $USER_COMPLETION_DIR"
    mkdir -p "$USER_COMPLETION_DIR"
    cp "$COMPLETION_DIR/jarvis-completion.bash" "$USER_COMPLETION_DIR/jarvis"
    
    # Check if bash-completion is sourced in user's shell
    BASH_COMPLETION_SOURCED=false
    
    for bashrc in "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
        if [[ -f "$bashrc" ]] && grep -q "bash-completion" "$bashrc"; then
            BASH_COMPLETION_SOURCED=true
            break
        fi
    done
    
    if [[ "$BASH_COMPLETION_SOURCED" == false ]]; then
        print_warning "bash-completion may not be enabled in your shell"
        print_status "You may need to add this to your ~/.bashrc:"
        echo "    # Enable bash completion"
        echo "    if [[ -f /usr/share/bash-completion/bash_completion ]]; then"
        echo "        . /usr/share/bash-completion/bash_completion"
        echo "    elif [[ -f /etc/bash_completion ]]; then"
        echo "        . /etc/bash_completion"
        echo "    fi"
        echo ""
    fi
    
    print_status "User-specific installation complete!"
    print_status "Restart your shell or run: source ~/.bashrc"
fi

# Test if jarvis command is available
if command -v jarvis >/dev/null 2>&1; then
    print_status "jarvis command found at: $(which jarvis)"
else
    print_warning "jarvis command not found in PATH"
    print_status "Make sure to install jarvis first: pip install ."
fi

# Test if helper script is accessible
JARVIS_BIN_DIR="$(dirname "$(which jarvis 2>/dev/null)" 2>/dev/null || echo "")"
if [[ -n "$JARVIS_BIN_DIR" ]] && [[ -x "$JARVIS_BIN_DIR/jarvis-completion-helper" ]]; then
    print_status "Completion helper found at: $JARVIS_BIN_DIR/jarvis-completion-helper"
elif [[ -x "$BIN_DIR/jarvis-completion-helper" ]]; then
    print_status "Completion helper found at: $BIN_DIR/jarvis-completion-helper"
else
    print_warning "Completion helper not found in expected locations"
    print_status "Completion may not work until jarvis is properly installed"
fi

print_status "Installation complete!"
print_status ""
print_status "To test completion, try:"
print_status "  jarvis pipeline ap<TAB>     # Should complete to 'append'"
print_status "  jarvis pipeline append gr<TAB>  # Should show packages starting with 'gr'"
print_status ""
print_status "If completion doesn't work immediately:"
print_status "  1. Restart your terminal or run: source ~/.bashrc"
print_status "  2. Make sure bash-completion is installed and enabled"
print_status "  3. Ensure jarvis is in your PATH"