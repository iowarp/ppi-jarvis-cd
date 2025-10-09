import unittest
import tempfile
import os
import socket
import sys

# Add the project root to the path so we can import jarvis_cd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from jarvis_cd.util.hostfile import Hostfile


class TestHostfile(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up any temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
        
    def test_default_constructor(self):
        """Test default constructor creates localhost hostfile"""
        hostfile = Hostfile()
        
        self.assertEqual(len(hostfile), 1)
        self.assertEqual(hostfile.hosts, ['localhost'])
        self.assertEqual(len(hostfile.hosts_ip), 1)
        self.assertTrue(hostfile.is_local())
        
    def test_constructor_with_hosts_list(self):
        """Test constructor with explicit hosts list"""
        hosts = ['host1', 'host2', 'host3']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        self.assertEqual(len(hostfile), 3)
        self.assertEqual(hostfile.hosts, hosts)
        self.assertEqual(hostfile.hosts_ip, [])
        self.assertFalse(hostfile.is_local())
        
    def test_constructor_with_hosts_and_ips(self):
        """Test constructor with both hosts and IPs"""
        hosts = ['host1', 'host2']
        ips = ['192.168.1.1', '192.168.1.2']
        hostfile = Hostfile(hosts=hosts, hosts_ip=ips, find_ips=False)
        
        self.assertEqual(hostfile.hosts, hosts)
        self.assertEqual(hostfile.hosts_ip, ips)
        
    def test_simple_host_pattern(self):
        """Test simple hostname without brackets"""
        text = "ares-comp-01"
        hostfile = Hostfile(text=text, find_ips=False)
        
        self.assertEqual(len(hostfile), 1)
        self.assertEqual(hostfile.hosts, ['ares-comp-01'])
        
    def test_bracket_range_pattern(self):
        """Test bracket range expansion like [02-04]"""
        text = "ares-comp-[02-04]"
        hostfile = Hostfile(text=text, find_ips=False)
        
        expected = ['ares-comp-02', 'ares-comp-03', 'ares-comp-04']
        self.assertEqual(len(hostfile), 3)
        self.assertEqual(hostfile.hosts, expected)
        
    def test_bracket_list_pattern(self):
        """Test bracket list expansion like [05,07,09]"""
        text = "ares-comp-[05,07,09]"
        hostfile = Hostfile(text=text, find_ips=False)
        
        expected = ['ares-comp-05', 'ares-comp-07', 'ares-comp-09']
        self.assertEqual(len(hostfile), 3)
        self.assertEqual(hostfile.hosts, expected)
        
    def test_complex_bracket_pattern(self):
        """Test complex bracket pattern with ranges and lists"""
        text = "ares-comp-[05-09,11,12-14]-40g"
        hostfile = Hostfile(text=text, find_ips=False)
        
        expected = [
            'ares-comp-05-40g', 'ares-comp-06-40g', 'ares-comp-07-40g',
            'ares-comp-08-40g', 'ares-comp-09-40g', 'ares-comp-11-40g',
            'ares-comp-12-40g', 'ares-comp-13-40g', 'ares-comp-14-40g'
        ]
        self.assertEqual(len(hostfile), 9)
        self.assertEqual(hostfile.hosts, expected)
        
    def test_zero_padded_ranges(self):
        """Test that zero-padding is preserved in ranges"""
        text = "node-[001-003]"
        hostfile = Hostfile(text=text, find_ips=False)
        
        expected = ['node-001', 'node-002', 'node-003']
        self.assertEqual(hostfile.hosts, expected)
        
    def test_alphabetic_ranges(self):
        """Test alphabetic range expansion like [a-c]"""
        text = "server-[a-c]"
        hostfile = Hostfile(text=text, find_ips=False)
        
        expected = ['server-a', 'server-b', 'server-c']
        self.assertEqual(hostfile.hosts, expected)
        
    def test_uppercase_alphabetic_ranges(self):
        """Test uppercase alphabetic range expansion like [A-C]"""
        text = "server-[A-C]"
        hostfile = Hostfile(text=text, find_ips=False)
        
        expected = ['server-A', 'server-B', 'server-C']
        self.assertEqual(hostfile.hosts, expected)
        
    def test_multiple_lines(self):
        """Test hostfile with multiple lines"""
        text = """ares-comp-01
ares-comp-[02-04]
ares-comp-[05-09,11,12-14]-40g"""
        hostfile = Hostfile(text=text, find_ips=False)
        
        # Should have 1 + 3 + 9 = 13 hosts
        self.assertEqual(len(hostfile), 13)
        self.assertIn('ares-comp-01', hostfile.hosts)
        self.assertIn('ares-comp-02', hostfile.hosts)
        self.assertIn('ares-comp-05-40g', hostfile.hosts)
        
    def test_file_loading(self):
        """Test loading hostfile from filesystem"""
        content = """host1
host2
host-[10-12]"""
        
        # Create temporary hostfile
        hostfile_path = os.path.join(self.temp_dir, 'test_hostfile.txt')
        with open(hostfile_path, 'w') as f:
            f.write(content)
            
        hostfile = Hostfile(path=hostfile_path, find_ips=False)
        
        expected = ['host1', 'host2', 'host-10', 'host-11', 'host-12']
        self.assertEqual(len(hostfile), 5)
        self.assertEqual(hostfile.hosts, expected)
        
    def test_file_not_found(self):
        """Test error when hostfile doesn't exist"""
        with self.assertRaises(FileNotFoundError):
            Hostfile(path='/nonexistent/hostfile.txt')
            
    def test_subset(self):
        """Test subset functionality"""
        hosts = ['host1', 'host2', 'host3', 'host4']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        subset = hostfile.subset(2)
        
        self.assertEqual(len(subset), 2)
        self.assertEqual(subset.hosts, ['host1', 'host2'])
        
    def test_copy(self):
        """Test copy functionality"""
        hosts = ['host1', 'host2']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        copy = hostfile.copy()
        
        self.assertEqual(len(copy), len(hostfile))
        self.assertEqual(copy.hosts, hostfile.hosts)
        self.assertIsNot(copy.hosts, hostfile.hosts)  # Should be different objects
        
    def test_is_local_localhost(self):
        """Test is_local with localhost"""
        hostfile = Hostfile(hosts=['localhost'], find_ips=False)
        self.assertTrue(hostfile.is_local())
        
    def test_is_local_empty(self):
        """Test is_local with empty hostfile"""
        hostfile = Hostfile(hosts=[], find_ips=False)
        self.assertTrue(hostfile.is_local())
        
    def test_is_local_multiple_hosts(self):
        """Test is_local with multiple hosts"""
        hostfile = Hostfile(hosts=['host1', 'host2'], find_ips=False)
        self.assertFalse(hostfile.is_local())
        
    def test_save(self):
        """Test saving hostfile to filesystem"""
        hosts = ['host1', 'host2', 'host3']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        save_path = os.path.join(self.temp_dir, 'saved_hostfile.txt')
        hostfile.save(save_path)
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(save_path))
        with open(save_path, 'r') as f:
            content = f.read().strip()
        
        self.assertEqual(content, 'host1\nhost2\nhost3')
        
    def test_list(self):
        """Test list functionality"""
        hosts = ['host1', 'host2']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        host_list = hostfile.list()
        
        self.assertEqual(len(host_list), 2)
        self.assertIsInstance(host_list[0], Hostfile)
        self.assertEqual(host_list[0].hosts, ['host1'])
        self.assertEqual(host_list[1].hosts, ['host2'])
        
    def test_enumerate(self):
        """Test enumerate functionality"""
        hosts = ['host1', 'host2']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        enumerated = list(hostfile.enumerate())
        
        self.assertEqual(len(enumerated), 2)
        self.assertEqual(enumerated[0][0], 0)
        self.assertEqual(enumerated[0][1].hosts, ['host1'])
        self.assertEqual(enumerated[1][0], 1)
        self.assertEqual(enumerated[1][1].hosts, ['host2'])
        
    def test_host_str(self):
        """Test host_str functionality"""
        hosts = ['host1', 'host2', 'host3']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        self.assertEqual(hostfile.host_str(), 'host1,host2,host3')
        self.assertEqual(hostfile.host_str('|'), 'host1|host2|host3')
        
    def test_ip_str(self):
        """Test ip_str functionality"""
        hosts = ['host1', 'host2']
        ips = ['192.168.1.1', '192.168.1.2']
        hostfile = Hostfile(hosts=hosts, hosts_ip=ips, find_ips=False)
        
        self.assertEqual(hostfile.ip_str(), '192.168.1.1,192.168.1.2')
        self.assertEqual(hostfile.ip_str('|'), '192.168.1.1|192.168.1.2')
        
    def test_len(self):
        """Test __len__ functionality"""
        hostfile = Hostfile(hosts=['host1', 'host2', 'host3'], find_ips=False)
        self.assertEqual(len(hostfile), 3)
        
    def test_iter(self):
        """Test __iter__ functionality"""
        hosts = ['host1', 'host2', 'host3']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        iterated_hosts = list(hostfile)
        self.assertEqual(iterated_hosts, hosts)
        
    def test_getitem(self):
        """Test __getitem__ functionality"""
        hosts = ['host1', 'host2', 'host3']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        self.assertEqual(hostfile[0], 'host1')
        self.assertEqual(hostfile[1], 'host2')
        self.assertEqual(hostfile[-1], 'host3')
        
    def test_str_repr(self):
        """Test string representations"""
        hosts = ['host1', 'host2']
        hostfile = Hostfile(hosts=hosts, find_ips=False)
        
        str_repr = str(hostfile)
        self.assertIn('2 hosts', str_repr)
        self.assertIn('host1,host2', str_repr)
        
        detailed_repr = repr(hostfile)
        self.assertIn('hosts=', detailed_repr)
        self.assertIn('hosts_ip=', detailed_repr)
        
    def test_ip_resolution_localhost(self):
        """Test IP resolution for localhost"""
        hostfile = Hostfile()  # Default constructor with find_ips=True
        
        self.assertEqual(len(hostfile.hosts_ip), 1)
        # Should resolve to some localhost IP
        self.assertIsNotNone(hostfile.hosts_ip[0])
        
    def test_empty_lines_ignored(self):
        """Test that empty lines are ignored in hostfile text"""
        text = """host1

host2

host3
"""
        hostfile = Hostfile(text=text, find_ips=False)
        
        self.assertEqual(len(hostfile), 3)
        self.assertEqual(hostfile.hosts, ['host1', 'host2', 'host3'])
        
    def test_no_find_ips(self):
        """Test constructor with find_ips=False"""
        hostfile = Hostfile(hosts=['host1', 'host2'], find_ips=False)
        
        self.assertEqual(hostfile.hosts_ip, [])


if __name__ == '__main__':
    unittest.main()