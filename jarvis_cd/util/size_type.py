"""
Size type utility for Jarvis-CD.
Converts size strings (like "1k", "2M", "10G") to integer byte values using binary multipliers.
"""

import re
from typing import Union


class SizeType:
    """
    Utility class for converting size strings to integer byte values.
    
    Supports binary multipliers (powers of 2):
    - k/K: 1024 (1 << 10)
    - m/M: 1048576 (1 << 20) 
    - g/G: 1073741824 (1 << 30)
    - t/T: 1099511627776 (1 << 40)
    
    Examples:
        SizeType("1k")    -> 1024
        SizeType("2M")    -> 2097152  
        SizeType("10g")   -> 10737418240
        SizeType("100")   -> 100 (no multiplier)
    """
    
    # Binary multipliers (powers of 2)
    MULTIPLIERS = {
        'k': 1 << 10,  # 1024
        'm': 1 << 20,  # 1048576
        'g': 1 << 30,  # 1073741824
        't': 1 << 40,  # 1099511627776
    }
    
    def __init__(self, size_str: Union[str, int, float]):
        """
        Initialize SizeType with a size string, integer, or float.
        
        :param size_str: Size specification (e.g., "1k", "2M", "100", 1024)
        """
        if isinstance(size_str, (int, float)):
            self._bytes = int(size_str)
        else:
            self._bytes = self._parse_size_string(str(size_str))
    
    def _parse_size_string(self, size_str: str) -> int:
        """
        Parse a size string into integer bytes.
        
        :param size_str: Size string to parse
        :return: Size in bytes
        :raises ValueError: If the size string format is invalid
        """
        # Remove whitespace
        size_str = size_str.strip()
        
        if not size_str:
            raise ValueError("Empty size string")
        
        # Match number followed by optional multiplier (stricter pattern)
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([kmgtKMGT]?)(?:[bB].*)?$', size_str)
        
        if not match:
            raise ValueError(f"Invalid size format: '{size_str}'. Expected format: number[k|m|g|t]")
        
        number_str, multiplier = match.groups()
        
        try:
            # Parse the number (can be float, but must be positive)
            number = float(number_str)
            if number < 0:
                raise ValueError(f"Size cannot be negative: {number}")
        except ValueError as e:
            if "negative" in str(e):
                raise e
            raise ValueError(f"Invalid number: '{number_str}'")
        
        # Get multiplier (case-insensitive, look at first character)
        if multiplier:
            multiplier_key = multiplier[0].lower()
            if multiplier_key in self.MULTIPLIERS:
                multiplier_value = self.MULTIPLIERS[multiplier_key]
            else:
                raise ValueError(f"Unknown size multiplier: '{multiplier}'. Supported: k, m, g, t")
        else:
            multiplier_value = 1
        
        # Calculate final size in bytes
        total_bytes = number * multiplier_value
        
        # Return as integer
        return int(total_bytes)
    
    def __int__(self) -> int:
        """Convert to integer (bytes)."""
        return self._bytes
    
    def __float__(self) -> float:
        """Convert to float (bytes)."""
        return float(self._bytes)
    
    def __str__(self) -> str:
        """String representation shows bytes value."""
        return f"{self._bytes}B"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"SizeType({self._bytes} bytes)"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, SizeType):
            return self._bytes == other._bytes
        elif isinstance(other, (int, float)):
            return self._bytes == other
        return False
    
    def __lt__(self, other) -> bool:
        """Less than comparison."""
        if isinstance(other, SizeType):
            return self._bytes < other._bytes
        elif isinstance(other, (int, float)):
            return self._bytes < other
        return NotImplemented
    
    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self == other or self < other
    
    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if isinstance(other, SizeType):
            return self._bytes > other._bytes
        elif isinstance(other, (int, float)):
            return self._bytes > other
        return NotImplemented
    
    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self == other or self > other
    
    def __add__(self, other):
        """Addition operation."""
        if isinstance(other, SizeType):
            return SizeType(self._bytes + other._bytes)
        elif isinstance(other, (int, float)):
            return SizeType(self._bytes + other)
        return NotImplemented
    
    def __sub__(self, other):
        """Subtraction operation."""
        if isinstance(other, SizeType):
            return SizeType(self._bytes - other._bytes)
        elif isinstance(other, (int, float)):
            return SizeType(self._bytes - other)
        return NotImplemented
    
    def __mul__(self, other):
        """Multiplication operation."""
        if isinstance(other, (int, float)):
            return SizeType(self._bytes * other)
        return NotImplemented
    
    def __truediv__(self, other):
        """Division operation."""
        if isinstance(other, (int, float)):
            return SizeType(self._bytes / other)
        elif isinstance(other, SizeType):
            return self._bytes / other._bytes  # Return ratio as float
        return NotImplemented
    
    @property
    def bytes(self) -> int:
        """Get size in bytes."""
        return self._bytes
    
    def to_bytes(self) -> int:
        """
        Get size as integer bytes.
        
        :return: Size in bytes as integer
        """
        return self._bytes
    
    @property 
    def kilobytes(self) -> float:
        """Get size in kilobytes (1024 bytes)."""
        return self._bytes / (1 << 10)
    
    @property
    def megabytes(self) -> float:
        """Get size in megabytes (1024^2 bytes)."""
        return self._bytes / (1 << 20)
    
    @property
    def gigabytes(self) -> float:
        """Get size in gigabytes (1024^3 bytes)."""
        return self._bytes / (1 << 30)
    
    @property
    def terabytes(self) -> float:
        """Get size in terabytes (1024^4 bytes)."""
        return self._bytes / (1 << 40)
    
    def to_human_readable(self) -> str:
        """
        Convert to human-readable string format.
        
        :return: Human-readable size string (e.g., "1.5K", "2.0M")
        """
        if self._bytes == 0:
            return "0B"
        
        # Choose the largest unit that results in >= 1
        for unit, multiplier in [('T', 1 << 40), ('G', 1 << 30), ('M', 1 << 20), ('K', 1 << 10)]:
            if self._bytes >= multiplier:
                value = self._bytes / multiplier
                if value == int(value):
                    return f"{int(value)}{unit}"
                else:
                    return f"{value:.1f}{unit}"
        
        # Less than 1024 bytes
        return f"{self._bytes}B"
    
    @classmethod
    def parse(cls, size_str: Union[str, int, float]) -> 'SizeType':
        """
        Class method to parse a size string.
        
        :param size_str: Size specification
        :return: SizeType instance
        """
        return cls(size_str)
    
    @classmethod
    def from_bytes(cls, bytes_value: int) -> 'SizeType':
        """
        Create SizeType from byte value.
        
        :param bytes_value: Size in bytes
        :return: SizeType instance
        """
        return cls(bytes_value)
    
    @classmethod
    def from_kilobytes(cls, kb_value: float) -> 'SizeType':
        """Create SizeType from kilobytes."""
        return cls(int(kb_value * (1 << 10)))
    
    @classmethod
    def from_megabytes(cls, mb_value: float) -> 'SizeType':
        """Create SizeType from megabytes."""
        return cls(int(mb_value * (1 << 20)))
    
    @classmethod
    def from_gigabytes(cls, gb_value: float) -> 'SizeType':
        """Create SizeType from gigabytes."""
        return cls(int(gb_value * (1 << 30)))
    
    @classmethod
    def from_terabytes(cls, tb_value: float) -> 'SizeType':
        """Create SizeType from terabytes."""
        return cls(int(tb_value * (1 << 40)))


# Convenience functions for quick conversions
def size_to_bytes(size_str: Union[str, int, float]) -> int:
    """
    Convert size string to bytes.
    
    :param size_str: Size specification
    :return: Size in bytes
    """
    return SizeType(size_str).bytes


def human_readable_size(bytes_value: int) -> str:
    """
    Convert bytes to human-readable format.
    
    :param bytes_value: Size in bytes
    :return: Human-readable size string
    """
    return SizeType.from_bytes(bytes_value).to_human_readable()