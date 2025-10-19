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

    def test_size_type_from_string_tb(self):
        """Test SizeType from terabyte string"""
        size = SizeType('1T')
        self.assertEqual(size.bytes, 1 * 1024 * 1024 * 1024 * 1024)
        size2 = SizeType('2t')  # lowercase
        self.assertEqual(size2.bytes, 2 * 1024 * 1024 * 1024 * 1024)

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
        self.assertIn('B', str_rep)

    def test_size_type_repr(self):
        """Test repr representation of SizeType"""
        size = SizeType(2048)
        repr_str = repr(size)
        self.assertIn('SizeType', repr_str)
        self.assertIn('2048', repr_str)
        self.assertIn('bytes', repr_str)

    def test_size_type_comparison(self):
        """Test SizeType comparison operators"""
        size1 = SizeType('1k')
        size2 = SizeType('2k')
        size3 = SizeType('1024')  # Same as 1k

        self.assertLess(size1.bytes, size2.bytes)
        self.assertEqual(size1.bytes, size3.bytes)

    def test_equality_with_sizetype(self):
        """Test equality comparison with another SizeType"""
        size1 = SizeType(1024)
        size2 = SizeType('1k')
        size3 = SizeType(2048)

        self.assertEqual(size1, size2)
        self.assertNotEqual(size1, size3)

    def test_equality_with_int(self):
        """Test equality comparison with int"""
        size = SizeType(1024)
        self.assertEqual(size, 1024)
        self.assertNotEqual(size, 2048)

    def test_equality_with_float(self):
        """Test equality comparison with float"""
        size = SizeType(1536)
        self.assertEqual(size, 1536.0)
        self.assertNotEqual(size, 1536.5)

    def test_equality_with_other_type(self):
        """Test equality comparison with unsupported type returns False"""
        size = SizeType(1024)
        self.assertFalse(size == "1024")
        self.assertFalse(size == [1024])

    def test_less_than_comparison(self):
        """Test less than comparison"""
        size1 = SizeType(1024)
        size2 = SizeType(2048)

        # SizeType vs SizeType
        self.assertTrue(size1 < size2)
        self.assertFalse(size2 < size1)

        # SizeType vs int
        self.assertTrue(size1 < 2048)
        self.assertFalse(size1 < 512)

    def test_less_than_equal_comparison(self):
        """Test less than or equal comparison"""
        size1 = SizeType(1024)
        size2 = SizeType(1024)
        size3 = SizeType(2048)

        self.assertTrue(size1 <= size2)
        self.assertTrue(size1 <= size3)
        self.assertFalse(size3 <= size1)

    def test_greater_than_comparison(self):
        """Test greater than comparison"""
        size1 = SizeType(2048)
        size2 = SizeType(1024)

        # SizeType vs SizeType
        self.assertTrue(size1 > size2)
        self.assertFalse(size2 > size1)

        # SizeType vs int
        self.assertTrue(size1 > 1024)
        self.assertFalse(size1 > 4096)

    def test_greater_than_equal_comparison(self):
        """Test greater than or equal comparison"""
        size1 = SizeType(1024)
        size2 = SizeType(1024)
        size3 = SizeType(512)

        self.assertTrue(size1 >= size2)
        self.assertTrue(size1 >= size3)
        self.assertFalse(size3 >= size1)

    def test_addition_with_sizetype(self):
        """Test addition with another SizeType"""
        size1 = SizeType(1024)
        size2 = SizeType(512)
        result = size1 + size2

        self.assertIsInstance(result, SizeType)
        self.assertEqual(result.bytes, 1536)

    def test_addition_with_int(self):
        """Test addition with int"""
        size = SizeType(1024)
        result = size + 512

        self.assertIsInstance(result, SizeType)
        self.assertEqual(result.bytes, 1536)

    def test_subtraction_with_sizetype(self):
        """Test subtraction with another SizeType"""
        size1 = SizeType(2048)
        size2 = SizeType(1024)
        result = size1 - size2

        self.assertIsInstance(result, SizeType)
        self.assertEqual(result.bytes, 1024)

    def test_subtraction_with_int(self):
        """Test subtraction with int"""
        size = SizeType(2048)
        result = size - 1024

        self.assertIsInstance(result, SizeType)
        self.assertEqual(result.bytes, 1024)

    def test_multiplication(self):
        """Test multiplication"""
        size = SizeType(1024)
        result = size * 2

        self.assertIsInstance(result, SizeType)
        self.assertEqual(result.bytes, 2048)

        result2 = size * 1.5
        self.assertEqual(result2.bytes, 1536)

    def test_division_with_number(self):
        """Test division with int or float"""
        size = SizeType(2048)
        result = size / 2

        self.assertIsInstance(result, SizeType)
        self.assertEqual(result.bytes, 1024)

        result2 = size / 4.0
        self.assertEqual(result2.bytes, 512)

    def test_division_with_sizetype(self):
        """Test division with SizeType returns ratio as float"""
        size1 = SizeType(2048)
        size2 = SizeType(1024)
        result = size1 / size2

        self.assertIsInstance(result, float)
        self.assertEqual(result, 2.0)

    def test_int_conversion(self):
        """Test conversion to int"""
        size = SizeType('1k')
        self.assertEqual(int(size), 1024)

    def test_float_conversion(self):
        """Test conversion to float"""
        size = SizeType('1k')
        self.assertEqual(float(size), 1024.0)

    def test_bytes_property(self):
        """Test bytes property"""
        size = SizeType('2k')
        self.assertEqual(size.bytes, 2048)

    def test_to_bytes_method(self):
        """Test to_bytes method"""
        size = SizeType('3k')
        self.assertEqual(size.to_bytes(), 3072)

    def test_kilobytes_property(self):
        """Test kilobytes property"""
        size = SizeType(2048)
        self.assertEqual(size.kilobytes, 2.0)

    def test_megabytes_property(self):
        """Test megabytes property"""
        size = SizeType('2M')
        self.assertEqual(size.megabytes, 2.0)

    def test_gigabytes_property(self):
        """Test gigabytes property"""
        size = SizeType('3G')
        self.assertEqual(size.gigabytes, 3.0)

    def test_terabytes_property(self):
        """Test terabytes property"""
        size = SizeType('1T')
        self.assertEqual(size.terabytes, 1.0)

    def test_parse_classmethod(self):
        """Test parse class method"""
        size = SizeType.parse('5M')
        self.assertIsInstance(size, SizeType)
        self.assertEqual(size.bytes, 5 * 1024 * 1024)

    def test_from_bytes_classmethod(self):
        """Test from_bytes class method"""
        size = SizeType.from_bytes(4096)
        self.assertIsInstance(size, SizeType)
        self.assertEqual(size.bytes, 4096)

    def test_from_kilobytes_classmethod(self):
        """Test from_kilobytes class method"""
        size = SizeType.from_kilobytes(5)
        self.assertEqual(size.bytes, 5 * 1024)

    def test_from_megabytes_classmethod(self):
        """Test from_megabytes class method"""
        size = SizeType.from_megabytes(3)
        self.assertEqual(size.bytes, 3 * 1024 * 1024)

    def test_from_gigabytes_classmethod(self):
        """Test from_gigabytes class method"""
        size = SizeType.from_gigabytes(2)
        self.assertEqual(size.bytes, 2 * 1024 * 1024 * 1024)

    def test_from_terabytes_classmethod(self):
        """Test from_terabytes class method"""
        size = SizeType.from_terabytes(1)
        self.assertEqual(size.bytes, 1024 * 1024 * 1024 * 1024)

    def test_empty_string_error(self):
        """Test empty string raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            SizeType('')
        self.assertIn('Empty', str(ctx.exception))

    def test_whitespace_string_error(self):
        """Test whitespace-only string raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            SizeType('   ')
        self.assertIn('Empty', str(ctx.exception))

    def test_invalid_format_error(self):
        """Test invalid format raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            SizeType('abc')
        self.assertIn('Invalid size format', str(ctx.exception))

    def test_negative_number_error(self):
        """Test negative number raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            SizeType('-10')
        # Negative numbers are caught by regex pattern, not specific negative check
        self.assertIn('Invalid size format', str(ctx.exception))

    def test_unknown_multiplier_error(self):
        """Test unknown multiplier raises ValueError"""
        # The regex pattern only accepts k/m/g/t, so this should fail at pattern match
        with self.assertRaises(ValueError) as ctx:
            SizeType('10X')
        self.assertIn('Invalid size format', str(ctx.exception))

    def test_to_human_readable_zero(self):
        """Test human readable format for zero"""
        size = SizeType(0)
        self.assertEqual(size.to_human_readable(), '0B')

    def test_to_human_readable_bytes(self):
        """Test human readable format for bytes"""
        size = SizeType(512)
        self.assertEqual(size.to_human_readable(), '512B')

    def test_to_human_readable_kilobytes(self):
        """Test human readable format for kilobytes"""
        size = SizeType(1024)
        self.assertEqual(size.to_human_readable(), '1K')

        size2 = SizeType(int(1.5 * 1024))
        self.assertEqual(size2.to_human_readable(), '1.5K')

    def test_to_human_readable_megabytes(self):
        """Test human readable format for megabytes"""
        size = SizeType(2 * 1024 * 1024)
        self.assertEqual(size.to_human_readable(), '2M')

    def test_to_human_readable_gigabytes(self):
        """Test human readable format for gigabytes"""
        size = SizeType(3 * 1024 * 1024 * 1024)
        self.assertEqual(size.to_human_readable(), '3G')

    def test_to_human_readable_terabytes(self):
        """Test human readable format for terabytes"""
        size = SizeType(2 * 1024 * 1024 * 1024 * 1024)
        self.assertEqual(size.to_human_readable(), '2T')

    def test_whitespace_in_string(self):
        """Test size string with whitespace"""
        size = SizeType('  10k  ')
        self.assertEqual(size.bytes, 10 * 1024)

    def test_uppercase_and_lowercase_multipliers(self):
        """Test both uppercase and lowercase multipliers"""
        size_k = SizeType('1k')
        size_K = SizeType('1K')
        self.assertEqual(size_k.bytes, size_K.bytes)

        size_m = SizeType('1m')
        size_M = SizeType('1M')
        self.assertEqual(size_m.bytes, size_M.bytes)

    def test_decimal_numbers(self):
        """Test decimal numbers with multipliers"""
        size = SizeType('1.5k')
        self.assertEqual(size.bytes, int(1.5 * 1024))

        size2 = SizeType('2.75M')
        self.assertEqual(size2.bytes, int(2.75 * 1024 * 1024))

    def test_with_b_suffix(self):
        """Test strings with 'B' or 'bytes' suffix"""
        size1 = SizeType('10kB')
        self.assertEqual(size1.bytes, 10 * 1024)

        size2 = SizeType('5MB')
        self.assertEqual(size2.bytes, 5 * 1024 * 1024)

    def test_notimplemented_comparisons(self):
        """Test comparison with unsupported types returns NotImplemented"""
        size = SizeType(1024)
        # These should return NotImplemented, which Python handles
        result = size.__lt__("1024")
        self.assertEqual(result, NotImplemented)

        result = size.__gt__("1024")
        self.assertEqual(result, NotImplemented)

    def test_notimplemented_arithmetic(self):
        """Test arithmetic with unsupported types returns NotImplemented"""
        size = SizeType(1024)

        # Addition with unsupported type
        result = size.__add__("1024")
        self.assertEqual(result, NotImplemented)

        # Subtraction with unsupported type
        result = size.__sub__("1024")
        self.assertEqual(result, NotImplemented)

        # Multiplication with unsupported type
        result = size.__mul__("2")
        self.assertEqual(result, NotImplemented)

        # Division with unsupported type
        result = size.__truediv__("2")
        self.assertEqual(result, NotImplemented)


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
