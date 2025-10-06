"""
Logging utilities with color support for Jarvis.
"""
import sys
from enum import Enum


class Color(Enum):
    """Color codes for terminal output"""
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Light colors
    LIGHT_BLACK = '\033[90m'
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_MAGENTA = '\033[95m'
    LIGHT_CYAN = '\033[96m'
    LIGHT_WHITE = '\033[97m'
    
    # Special
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger:
    """
    Logger class with color support for terminal output.
    """
    
    def __init__(self, enable_colors: bool = True):
        """
        Initialize logger.
        
        :param enable_colors: Whether to enable color output (auto-detects TTY)
        """
        self.enable_colors = enable_colors and sys.stdout.isatty()
        
    def print(self, color: Color, message: str, file=None, end: str = '\n'):
        """
        Print a colored message to the terminal.

        :param color: Color to use for the message
        :param message: Message to print
        :param file: File to write to (default: stdout)
        :param end: String appended after the message
        """
        if file is None:
            file = sys.stdout

        if self.enable_colors:
            formatted_message = f"{color.value}{message}{Color.RESET.value}"
        else:
            formatted_message = message

        print(formatted_message, file=file, end=end, flush=True)
        
    def info(self, message: str, file=None, end: str = '\n'):
        """Print an info message in default color"""
        print(message, file=file, end=end, flush=True)
        
    def success(self, message: str, file=None, end: str = '\n'):
        """Print a success message in green"""
        self.print(Color.GREEN, message, file=file, end=end)
        
    def warning(self, message: str, file=None, end: str = '\n'):
        """Print a warning message in yellow"""
        self.print(Color.YELLOW, message, file=file, end=end)
        
    def error(self, message: str, file=None, end: str = '\n'):
        """Print an error message in red"""
        self.print(Color.RED, message, file=file, end=end)
        
    def debug(self, message: str, file=None, end: str = '\n'):
        """Print a debug message in light black (gray)"""
        self.print(Color.LIGHT_BLACK, message, file=file, end=end)
        
    def pipeline(self, message: str, file=None, end: str = '\n'):
        """Print a pipeline phase message in green"""
        self.print(Color.GREEN, message, file=file, end=end)
        
    def package(self, message: str, file=None, end: str = '\n'):
        """Print a package operation message in light green"""
        self.print(Color.LIGHT_GREEN, message, file=file, end=end)


# Global logger instance
logger = Logger()