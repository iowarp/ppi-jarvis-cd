"""
Tests for size_type.py - SizeType class and utilities
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.util.size_type import SizeType, size_to_bytes, human_readable_size


class TestSizeType(unittest.TestCase):
    """Tests for SizeType class"""

    def test_size_type_from_string_kb(self):
        """Test SizeType from kilobyte string"""
        size = SizeType('10k')
        self.assertEqual(size.bytes, 10 * 1024)

    def test_size_type_from_string_mb(self):
        """Test SizeType from megabyte string"""
        size = SizeType('5M')
        self.assertEqual(size.bytes, 5 * 1024 * 1024)

    def test_size_type_from_string_gb(self):
        """Test SizeType from gigabyte string"""
        size = SizeType('2G')
        self.assertEqual(size.bytes, 2 * 1024 * 1024 * 1024)

    def test_size_type_from_int(self):
        """Test SizeType from integer (bytes)"""
        size = SizeType(1024)
        self.assertEqual(size.bytes, 1024)

    def test_size_type_from_float(self):
        """Test SizeType from float"""
        size = SizeType(1536.5)
        self.assertEqual(size.bytes, int(1536.5))

    def test_size_type_str_representation(self):
        """Test string representation of SizeType"""
        size = SizeType('1M')
        str_rep = str(size)
        self.assertIn('1048576', str_rep)  # 1M in bytes

    def test_size_type_comparison(self):
        """Test SizeType comparison operators"""
        size1 = SizeType('1k')
        size2 = SizeType('2k')
        size3 = SizeType('1024')  # Same as 1k

        self.assertLess(size1.bytes, size2.bytes)
        self.assertEqual(size1.bytes, size3.bytes)


class TestSizeToBytes(unittest.TestCase):
    """Tests for size_to_bytes function"""

    def test_bytes_suffix(self):
        """Test conversion with B suffix"""
        self.assertEqual(size_to_bytes('100B'), 100)
        self.assertEqual(size_to_bytes('100'), 100)

    def test_kilobyte_suffix(self):
        """Test conversion with k/K suffix"""
        self.assertEqual(size_to_bytes('1k'), 1024)
        self.assertEqual(size_to_bytes('1K'), 1024)
        self.assertEqual(size_to_bytes('10k'), 10 * 1024)

    def test_megabyte_suffix(self):
        """Test conversion with M suffix"""
        self.assertEqual(size_to_bytes('1M'), 1024 * 1024)
        self.assertEqual(size_to_bytes('5M'), 5 * 1024 * 1024)

    def test_gigabyte_suffix(self):
        """Test conversion with G suffix"""
        self.assertEqual(size_to_bytes('1G'), 1024 * 1024 * 1024)
        self.assertEqual(size_to_bytes('2G'), 2 * 1024 * 1024 * 1024)

    def test_terabyte_suffix(self):
        """Test conversion with T suffix"""
        self.assertEqual(size_to_bytes('1T'), 1024 * 1024 * 1024 * 1024)

    def test_integer_input(self):
        """Test integer input returns as-is"""
        self.assertEqual(size_to_bytes(1024), 1024)
        self.assertEqual(size_to_bytes(5000), 5000)

    def test_float_input(self):
        """Test float input returns int"""
        self.assertEqual(size_to_bytes(1536.7), 1536)

    def test_decimal_with_suffix(self):
        """Test decimal numbers with suffix"""
        self.assertEqual(size_to_bytes('1.5k'), int(1.5 * 1024))
        self.assertEqual(size_to_bytes('2.5M'), int(2.5 * 1024 * 1024))


class TestHumanReadableSize(unittest.TestCase):
    """Tests for human_readable_size function"""

    def test_bytes_range(self):
        """Test formatting in bytes range"""
        result = human_readable_size(512)
        self.assertIn('512', result)
        self.assertIn('B', result)

    def test_kilobytes_range(self):
        """Test formatting in kilobytes range"""
        result = human_readable_size(2048)  # 2 KB
        self.assertIn('2', result)
        self.assertIn('K', result)

    def test_megabytes_range(self):
        """Test formatting in megabytes range"""
        result = human_readable_size(5 * 1024 * 1024)  # 5 MB
        self.assertIn('5', result)
        self.assertIn('M', result)

    def test_gigabytes_range(self):
        """Test formatting in gigabytes range"""
        result = human_readable_size(3 * 1024 * 1024 * 1024)  # 3 GB
        self.assertIn('3', result)
        self.assertIn('G', result)

    def test_terabytes_range(self):
        """Test formatting in terabytes range"""
        result = human_readable_size(2 * 1024 * 1024 * 1024 * 1024)  # 2 TB
        self.assertIn('2', result)
        self.assertIn('T', result)

    def test_zero_bytes(self):
        """Test zero bytes"""
        result = human_readable_size(0)
        self.assertIn('0', result)

    def test_fractional_sizes(self):
        """Test fractional sizes"""
        result = human_readable_size(int(1.5 * 1024))  # 1.5 KB
        self.assertIn('K', result)


if __name__ == '__main__':
    unittest.main()
