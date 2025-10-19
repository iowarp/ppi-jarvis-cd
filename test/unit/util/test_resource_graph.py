"""
Comprehensive unit tests for resource_graph.py module
Tests resource graph construction, analysis, filtering, and serialization
"""
import unittest
import sys
import os
import tempfile
import json
import yaml
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from jarvis_cd.util.resource_graph import ResourceGraph


class TestResourceGraphInitialization(unittest.TestCase):
    """Tests for ResourceGraph initialization"""

    def test_init_empty_graph(self):
        """Test ResourceGraph initialization creates empty structures"""
        graph = ResourceGraph()
        self.assertEqual(graph.nodes, {})
        self.assertEqual(graph.common_mounts, {})

    def test_init_no_arguments(self):
        """Test ResourceGraph can be initialized without arguments"""
        graph = ResourceGraph()
        self.assertIsInstance(graph.nodes, dict)
        self.assertIsInstance(graph.common_mounts, dict)


class TestResourceGraphAddNodeData(unittest.TestCase):
    """Tests for adding node data to resource graph"""

    def setUp(self):
        """Set up test resource graph"""
        self.graph = ResourceGraph()

    def test_add_single_node_single_device(self):
        """Test adding a single device to a single node"""
        resource_data = {
            'fs': [{
                'device': '/dev/sda1',
                'mount': '/mnt/data',
                'fs_type': 'ext4',
                'avail': '100G',
                'dev_type': 'ssd',
                'model': 'Samsung 970'
            }]
        }
        self.graph.add_node_data('node1', resource_data)

        self.assertIn('node1', self.graph.nodes)
        self.assertEqual(len(self.graph.nodes['node1']), 1)
        self.assertEqual(self.graph.nodes['node1'][0]['device'], '/dev/sda1')
        self.assertEqual(self.graph.nodes['node1'][0]['hostname'], 'node1')

    def test_add_single_node_multiple_devices(self):
        """Test adding multiple devices to a single node"""
        resource_data = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/mnt/data1', 'dev_type': 'ssd'},
                {'device': '/dev/sdb1', 'mount': '/mnt/data2', 'dev_type': 'hdd'},
                {'device': '/dev/sdc1', 'mount': '/mnt/data3', 'dev_type': 'nvme'}
            ]
        }
        self.graph.add_node_data('node1', resource_data)

        self.assertEqual(len(self.graph.nodes['node1']), 3)
        device_names = [d['device'] for d in self.graph.nodes['node1']]
        self.assertIn('/dev/sda1', device_names)
        self.assertIn('/dev/sdb1', device_names)
        self.assertIn('/dev/sdc1', device_names)

    def test_add_multiple_nodes(self):
        """Test adding data for multiple nodes"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/shared'}]}
        data2 = {'fs': [{'device': '/dev/sdb1', 'mount': '/shared'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        self.assertEqual(len(self.graph.nodes), 2)
        self.assertIn('node1', self.graph.nodes)
        self.assertIn('node2', self.graph.nodes)

    def test_default_field_values(self):
        """Test that default field values are set correctly"""
        resource_data = {'fs': [{'device': '/dev/sda1'}]}
        self.graph.add_node_data('node1', resource_data)

        device = self.graph.nodes['node1'][0]
        self.assertEqual(device['mount'], '')
        self.assertEqual(device['fs_type'], 'unknown')
        self.assertEqual(device['avail'], '0B')
        self.assertEqual(device['dev_type'], 'unknown')
        self.assertEqual(device['model'], 'unknown')
        self.assertEqual(device['parent'], '')
        self.assertEqual(device['uuid'], '')
        self.assertFalse(device['needs_root'])
        # In single-node cluster, all mounts are marked as shared
        self.assertTrue(device['shared'])
        self.assertEqual(device['4k_randwrite_bw'], 'unknown')
        self.assertEqual(device['1m_seqwrite_bw'], 'unknown')

    def test_add_empty_fs_list(self):
        """Test adding node with empty filesystem list"""
        resource_data = {'fs': []}
        self.graph.add_node_data('node1', resource_data)

        self.assertIn('node1', self.graph.nodes)
        self.assertEqual(len(self.graph.nodes['node1']), 0)

    def test_add_node_without_fs_key(self):
        """Test adding node data without 'fs' key"""
        resource_data = {}
        self.graph.add_node_data('node1', resource_data)

        self.assertIn('node1', self.graph.nodes)
        self.assertEqual(len(self.graph.nodes['node1']), 0)


class TestResourceGraphCommonMounts(unittest.TestCase):
    """Tests for common mount analysis"""

    def setUp(self):
        """Set up test resource graph"""
        self.graph = ResourceGraph()

    def test_single_node_all_common(self):
        """Test that all mounts are common in single-node cluster"""
        data = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/mnt/data1'},
                {'device': '/dev/sdb1', 'mount': '/mnt/data2'}
            ]
        }
        self.graph.add_node_data('node1', data)

        common = self.graph.get_common_storage()
        self.assertEqual(len(common), 2)
        self.assertIn('/mnt/data1', common)
        self.assertIn('/mnt/data2', common)

    def test_multi_node_common_mounts(self):
        """Test detection of common mounts across multiple nodes"""
        data1 = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/shared'},
                {'device': '/dev/sdb1', 'mount': '/local1'}
            ]
        }
        data2 = {
            'fs': [
                {'device': '/dev/sdc1', 'mount': '/shared'},
                {'device': '/dev/sdd1', 'mount': '/local2'}
            ]
        }

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        common = self.graph.get_common_storage()
        self.assertEqual(len(common), 1)
        self.assertIn('/shared', common)
        self.assertEqual(len(common['/shared']), 2)

    def test_shared_flag_multi_node(self):
        """Test that shared flag is set for common mounts in multi-node"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/shared'}]}
        data2 = {'fs': [{'device': '/dev/sdb1', 'mount': '/shared'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        # Check that shared flag is True
        for device in self.graph.nodes['node1']:
            if device['mount'] == '/shared':
                self.assertTrue(device['shared'])
        for device in self.graph.nodes['node2']:
            if device['mount'] == '/shared':
                self.assertTrue(device['shared'])

    def test_shared_flag_single_node(self):
        """Test that shared flag is set for all mounts in single-node"""
        data = {'fs': [{'device': '/dev/sda1', 'mount': '/data'}]}
        self.graph.add_node_data('node1', data)

        self.assertTrue(self.graph.nodes['node1'][0]['shared'])

    def test_no_common_mounts(self):
        """Test when there are no common mounts across nodes"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/local1'}]}
        data2 = {'fs': [{'device': '/dev/sdb1', 'mount': '/local2'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        common = self.graph.get_common_storage()
        self.assertEqual(len(common), 0)

    def test_three_nodes_partial_overlap(self):
        """Test common mounts with three nodes and partial overlap"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/shared'}]}
        data2 = {'fs': [{'device': '/dev/sdb1', 'mount': '/shared'}]}
        data3 = {'fs': [{'device': '/dev/sdc1', 'mount': '/local'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)
        self.graph.add_node_data('node3', data3)

        common = self.graph.get_common_storage()
        self.assertEqual(len(common), 1)
        self.assertIn('/shared', common)
        self.assertEqual(len(common['/shared']), 2)


class TestResourceGraphGetters(unittest.TestCase):
    """Tests for getter methods"""

    def setUp(self):
        """Set up test resource graph with sample data"""
        self.graph = ResourceGraph()
        data1 = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/shared', 'dev_type': 'ssd'},
                {'device': '/dev/sdb1', 'mount': '/local1', 'dev_type': 'hdd'}
            ]
        }
        data2 = {
            'fs': [
                {'device': '/dev/sdc1', 'mount': '/shared', 'dev_type': 'ssd'}
            ]
        }
        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

    def test_get_node_storage(self):
        """Test getting storage for specific node"""
        storage = self.graph.get_node_storage('node1')
        self.assertEqual(len(storage), 2)

        storage2 = self.graph.get_node_storage('node2')
        self.assertEqual(len(storage2), 1)

    def test_get_node_storage_nonexistent(self):
        """Test getting storage for non-existent node"""
        storage = self.graph.get_node_storage('nonexistent')
        self.assertEqual(storage, [])

    def test_get_all_nodes(self):
        """Test getting list of all nodes"""
        nodes = self.graph.get_all_nodes()
        self.assertEqual(len(nodes), 2)
        self.assertIn('node1', nodes)
        self.assertIn('node2', nodes)

    def test_get_all_nodes_empty(self):
        """Test getting nodes from empty graph"""
        empty_graph = ResourceGraph()
        nodes = empty_graph.get_all_nodes()
        self.assertEqual(nodes, [])

    def test_get_common_storage_returns_copy(self):
        """Test that get_common_storage returns a copy"""
        common1 = self.graph.get_common_storage()
        common2 = self.graph.get_common_storage()

        # Modify one copy
        if common1:
            common1.clear()

        # Original should still have data
        self.assertGreater(len(self.graph.common_mounts), 0)


class TestResourceGraphSummary(unittest.TestCase):
    """Tests for storage summary statistics"""

    def setUp(self):
        """Set up test resource graph"""
        self.graph = ResourceGraph()

    def test_summary_empty_graph(self):
        """Test summary of empty graph"""
        summary = self.graph.get_storage_summary()

        self.assertEqual(summary['total_nodes'], 0)
        self.assertEqual(summary['total_devices'], 0)
        self.assertEqual(summary['common_mount_points'], 0)
        self.assertEqual(summary['device_types'], {})
        self.assertEqual(summary['filesystem_types'], {})

    def test_summary_single_node(self):
        """Test summary with single node"""
        data = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/data1', 'dev_type': 'ssd', 'fs_type': 'ext4'},
                {'device': '/dev/sdb1', 'mount': '/data2', 'dev_type': 'hdd', 'fs_type': 'xfs'}
            ]
        }
        self.graph.add_node_data('node1', data)

        summary = self.graph.get_storage_summary()
        self.assertEqual(summary['total_nodes'], 1)
        self.assertEqual(summary['total_devices'], 2)
        self.assertEqual(summary['common_mount_points'], 2)
        self.assertEqual(summary['device_types']['ssd'], 1)
        self.assertEqual(summary['device_types']['hdd'], 1)
        self.assertEqual(summary['filesystem_types']['ext4'], 1)
        self.assertEqual(summary['filesystem_types']['xfs'], 1)

    def test_summary_multiple_nodes(self):
        """Test summary with multiple nodes"""
        data1 = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/shared', 'dev_type': 'ssd', 'fs_type': 'ext4'},
                {'device': '/dev/sdb1', 'mount': '/local1', 'dev_type': 'hdd', 'fs_type': 'xfs'}
            ]
        }
        data2 = {
            'fs': [
                {'device': '/dev/sdc1', 'mount': '/shared', 'dev_type': 'ssd', 'fs_type': 'ext4'},
                {'device': '/dev/sdd1', 'mount': '/local2', 'dev_type': 'nvme', 'fs_type': 'btrfs'}
            ]
        }

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        summary = self.graph.get_storage_summary()
        self.assertEqual(summary['total_nodes'], 2)
        self.assertEqual(summary['total_devices'], 4)
        self.assertEqual(summary['common_mount_points'], 1)
        self.assertEqual(summary['device_types']['ssd'], 2)
        self.assertEqual(summary['device_types']['hdd'], 1)
        self.assertEqual(summary['device_types']['nvme'], 1)

    def test_summary_device_type_aggregation(self):
        """Test that device types are properly aggregated"""
        data1 = {'fs': [{'device': '/dev/sda', 'dev_type': 'ssd', 'fs_type': 'ext4'}]}
        data2 = {'fs': [{'device': '/dev/sdb', 'dev_type': 'ssd', 'fs_type': 'ext4'}]}
        data3 = {'fs': [{'device': '/dev/sdc', 'dev_type': 'hdd', 'fs_type': 'ext4'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)
        self.graph.add_node_data('node3', data3)

        summary = self.graph.get_storage_summary()
        self.assertEqual(summary['device_types']['ssd'], 2)
        self.assertEqual(summary['device_types']['hdd'], 1)


class TestResourceGraphFiltering(unittest.TestCase):
    """Tests for filtering operations"""

    def setUp(self):
        """Set up test resource graph with diverse devices"""
        self.graph = ResourceGraph()
        data1 = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/mnt/ssd1', 'dev_type': 'ssd'},
                {'device': '/dev/sdb1', 'mount': '/mnt/hdd1', 'dev_type': 'hdd'},
                {'device': '/dev/sdc1', 'mount': '/mnt/nvme1', 'dev_type': 'nvme'}
            ]
        }
        data2 = {
            'fs': [
                {'device': '/dev/sdd1', 'mount': '/mnt/ssd2', 'dev_type': 'ssd'},
                {'device': '/dev/sde1', 'mount': '/home/data', 'dev_type': 'hdd'}
            ]
        }
        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

    def test_filter_by_type_ssd(self):
        """Test filtering by SSD device type"""
        filtered = self.graph.filter_by_type('ssd')

        self.assertEqual(len(filtered), 2)
        self.assertEqual(len(filtered['node1']), 1)
        self.assertEqual(len(filtered['node2']), 1)
        self.assertEqual(filtered['node1'][0]['device'], '/dev/sda1')

    def test_filter_by_type_hdd(self):
        """Test filtering by HDD device type"""
        filtered = self.graph.filter_by_type('hdd')

        self.assertEqual(len(filtered), 2)
        self.assertEqual(len(filtered['node1']), 1)
        self.assertEqual(len(filtered['node2']), 1)

    def test_filter_by_type_nvme(self):
        """Test filtering by NVMe device type"""
        filtered = self.graph.filter_by_type('nvme')

        self.assertEqual(len(filtered), 1)
        self.assertIn('node1', filtered)
        self.assertEqual(len(filtered['node1']), 1)

    def test_filter_by_type_nonexistent(self):
        """Test filtering by non-existent device type"""
        filtered = self.graph.filter_by_type('tape')
        self.assertEqual(filtered, {})

    def test_filter_by_mount_pattern_mnt(self):
        """Test filtering by mount pattern '/mnt'"""
        filtered = self.graph.filter_by_mount_pattern('/mnt')

        self.assertEqual(len(filtered), 2)
        self.assertEqual(len(filtered['node1']), 3)
        self.assertEqual(len(filtered['node2']), 1)

    def test_filter_by_mount_pattern_home(self):
        """Test filtering by mount pattern '/home'"""
        filtered = self.graph.filter_by_mount_pattern('/home')

        self.assertEqual(len(filtered), 1)
        self.assertIn('node2', filtered)
        self.assertEqual(len(filtered['node2']), 1)

    def test_filter_by_mount_pattern_ssd(self):
        """Test filtering by mount pattern containing 'ssd'"""
        filtered = self.graph.filter_by_mount_pattern('ssd')

        self.assertEqual(len(filtered), 2)
        self.assertEqual(len(filtered['node1']), 1)
        self.assertEqual(len(filtered['node2']), 1)

    def test_filter_by_mount_pattern_no_match(self):
        """Test filtering with pattern that matches nothing"""
        filtered = self.graph.filter_by_mount_pattern('/nonexistent')
        self.assertEqual(filtered, {})


class TestResourceGraphSerialization(unittest.TestCase):
    """Tests for save/load operations"""

    def setUp(self):
        """Set up test resource graph and temp directory"""
        self.graph = ResourceGraph()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp directory"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_to_yaml(self):
        """Test saving resource graph to YAML file"""
        data = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/data', 'dev_type': 'ssd', 'avail': '100G'}
            ]
        }
        self.graph.add_node_data('node1', data)

        output_path = Path(self.temp_dir) / 'test.yaml'
        self.graph.save_to_file(output_path, format='yaml')

        self.assertTrue(output_path.exists())

        # Verify content
        with open(output_path, 'r') as f:
            loaded_data = yaml.safe_load(f)

        self.assertIn('fs', loaded_data)
        self.assertEqual(len(loaded_data['fs']), 1)

    def test_save_to_json(self):
        """Test saving resource graph to JSON file"""
        data = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/data', 'dev_type': 'ssd'}
            ]
        }
        self.graph.add_node_data('node1', data)

        output_path = Path(self.temp_dir) / 'test.json'
        self.graph.save_to_file(output_path, format='json')

        self.assertTrue(output_path.exists())

        # Verify content
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)

        self.assertIn('fs', loaded_data)

    def test_save_only_common_mounts(self):
        """Test that only common mounts are saved"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/shared'}]}
        data2 = {'fs': [
            {'device': '/dev/sdb1', 'mount': '/shared'},
            {'device': '/dev/sdc1', 'mount': '/local'}
        ]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        output_path = Path(self.temp_dir) / 'test.yaml'
        self.graph.save_to_file(output_path)

        with open(output_path, 'r') as f:
            loaded_data = yaml.safe_load(f)

        # Should only save /shared (common mount)
        self.assertEqual(len(loaded_data['fs']), 1)
        self.assertEqual(loaded_data['fs'][0]['mount'], '/shared')

    def test_save_removes_hostname(self):
        """Test that hostname is removed from saved data"""
        data = {'fs': [{'device': '/dev/sda1', 'mount': '/data'}]}
        self.graph.add_node_data('node1', data)

        output_path = Path(self.temp_dir) / 'test.yaml'
        self.graph.save_to_file(output_path)

        with open(output_path, 'r') as f:
            loaded_data = yaml.safe_load(f)

        self.assertNotIn('hostname', loaded_data['fs'][0])

    def test_load_from_yaml(self):
        """Test loading resource graph from YAML file"""
        yaml_content = {
            'fs': [
                {
                    'device': '/dev/sda1',
                    'mount': '/data',
                    'dev_type': 'ssd',
                    'fs_type': 'ext4',
                    'avail': '100G'
                }
            ]
        }

        yaml_path = Path(self.temp_dir) / 'test.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f)

        self.graph.load_from_file(yaml_path)

        self.assertEqual(len(self.graph.nodes), 1)
        self.assertIn('test', self.graph.nodes)  # Filename becomes hostname
        self.assertEqual(len(self.graph.nodes['test']), 1)
        self.assertEqual(self.graph.nodes['test'][0]['device'], '/dev/sda1')

    def test_load_from_json(self):
        """Test loading resource graph from JSON file"""
        json_content = {
            'fs': [
                {
                    'device': '/dev/sda1',
                    'mount': '/data',
                    'dev_type': 'ssd'
                }
            ]
        }

        json_path = Path(self.temp_dir) / 'test.json'
        with open(json_path, 'w') as f:
            json.dump(json_content, f)

        self.graph.load_from_file(json_path)

        self.assertEqual(len(self.graph.nodes), 1)
        self.assertIn('test', self.graph.nodes)

    def test_load_clears_existing_data(self):
        """Test that loading clears existing data"""
        data = {'fs': [{'device': '/dev/existing', 'mount': '/old'}]}
        self.graph.add_node_data('oldnode', data)

        yaml_content = {'fs': [{'device': '/dev/new', 'mount': '/new'}]}
        yaml_path = Path(self.temp_dir) / 'new.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f)

        self.graph.load_from_file(yaml_path)

        self.assertNotIn('oldnode', self.graph.nodes)
        self.assertIn('new', self.graph.nodes)

    def test_load_expands_environment_variables(self):
        """Test that environment variables in mount paths are expanded"""
        os.environ['TEST_MOUNT'] = '/expanded/path'

        yaml_content = {'fs': [{'device': '/dev/sda1', 'mount': '$TEST_MOUNT/data'}]}
        yaml_path = Path(self.temp_dir) / 'test.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f)

        self.graph.load_from_file(yaml_path)

        self.assertEqual(self.graph.nodes['test'][0]['mount'], '/expanded/path/data')

    def test_load_invalid_format_raises_error(self):
        """Test that loading invalid format raises ValueError"""
        yaml_content = {'invalid': 'no fs section'}
        yaml_path = Path(self.temp_dir) / 'invalid.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f)

        with self.assertRaises(ValueError) as context:
            self.graph.load_from_file(yaml_path)

        self.assertIn('Invalid resource graph format', str(context.exception))

    def test_save_load_roundtrip(self):
        """Test that save and load preserve data correctly"""
        data = {
            'fs': [
                {
                    'device': '/dev/sda1',
                    'mount': '/data',
                    'dev_type': 'ssd',
                    'fs_type': 'ext4',
                    'avail': '500G',
                    'model': 'Samsung 970'
                }
            ]
        }
        self.graph.add_node_data('node1', data)

        # Save
        save_path = Path(self.temp_dir) / 'roundtrip.yaml'
        self.graph.save_to_file(save_path)

        # Load into new graph
        new_graph = ResourceGraph()
        new_graph.load_from_file(save_path)

        # Verify data
        self.assertEqual(len(new_graph.nodes), 1)
        loaded_device = new_graph.nodes['roundtrip'][0]
        self.assertEqual(loaded_device['device'], '/dev/sda1')
        self.assertEqual(loaded_device['mount'], '/data')
        self.assertEqual(loaded_device['dev_type'], 'ssd')

    def test_save_empty_graph(self):
        """Test saving empty graph"""
        output_path = Path(self.temp_dir) / 'empty.yaml'
        self.graph.save_to_file(output_path)

        self.assertTrue(output_path.exists())

        with open(output_path, 'r') as f:
            loaded_data = yaml.safe_load(f)

        self.assertEqual(loaded_data['fs'], [])


class TestResourceGraphPrintMethods(unittest.TestCase):
    """Tests for print/display methods"""

    def setUp(self):
        """Set up test resource graph"""
        self.graph = ResourceGraph()

    def test_print_summary_empty(self):
        """Test print_summary with empty graph"""
        # Should not raise any errors
        self.graph.print_summary()

    def test_print_summary_with_data(self):
        """Test print_summary with actual data"""
        data = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/data', 'dev_type': 'ssd', 'fs_type': 'ext4'}
            ]
        }
        self.graph.add_node_data('node1', data)

        # Should not raise any errors
        self.graph.print_summary()

    def test_print_common_storage_empty(self):
        """Test print_common_storage with no common storage"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/local1'}]}
        data2 = {'fs': [{'device': '/dev/sdb1', 'mount': '/local2'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        # Should handle gracefully
        self.graph.print_common_storage()

    def test_print_common_storage_single_node(self):
        """Test print_common_storage with single node"""
        data = {'fs': [{'device': '/dev/sda1', 'mount': '/data'}]}
        self.graph.add_node_data('node1', data)

        # Should not raise any errors
        self.graph.print_common_storage()

    def test_print_common_storage_multi_node(self):
        """Test print_common_storage with multiple nodes"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/shared'}]}
        data2 = {'fs': [{'device': '/dev/sdb1', 'mount': '/shared'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node2', data2)

        # Should not raise any errors
        self.graph.print_common_storage()

    def test_print_common_storage_with_performance_info(self):
        """Test print_common_storage includes performance info"""
        data = {
            'fs': [{
                'device': '/dev/sda1',
                'mount': '/data',
                '4k_randwrite_bw': '500MB/s',
                '1m_seqwrite_bw': '2GB/s'
            }]
        }
        self.graph.add_node_data('node1', data)

        # Should not raise any errors
        self.graph.print_common_storage()

    def test_print_node_details_existing(self):
        """Test print_node_details for existing node"""
        data = {
            'fs': [
                {
                    'device': '/dev/sda1',
                    'mount': '/data',
                    'dev_type': 'ssd',
                    'fs_type': 'ext4',
                    'avail': '100G',
                    'model': 'Samsung 970',
                    '4k_randwrite_bw': '500MB/s',
                    '1m_seqwrite_bw': '2GB/s'
                }
            ]
        }
        self.graph.add_node_data('node1', data)

        # Should not raise any errors
        self.graph.print_node_details('node1')

    def test_print_node_details_nonexistent(self):
        """Test print_node_details for non-existent node"""
        # Should handle gracefully
        self.graph.print_node_details('nonexistent')

    def test_print_node_details_no_performance(self):
        """Test print_node_details without performance data"""
        data = {'fs': [{'device': '/dev/sda1', 'mount': '/data'}]}
        self.graph.add_node_data('node1', data)

        # Should not raise any errors
        self.graph.print_node_details('node1')


class TestResourceGraphEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling"""

    def setUp(self):
        """Set up test resource graph"""
        self.graph = ResourceGraph()

    def test_add_node_multiple_times(self):
        """Test adding data to same node multiple times"""
        data1 = {'fs': [{'device': '/dev/sda1', 'mount': '/data1'}]}
        data2 = {'fs': [{'device': '/dev/sdb1', 'mount': '/data2'}]}

        self.graph.add_node_data('node1', data1)
        self.graph.add_node_data('node1', data2)

        # Should accumulate devices
        self.assertEqual(len(self.graph.nodes['node1']), 2)

    def test_device_with_special_characters(self):
        """Test handling devices with special characters"""
        data = {
            'fs': [{
                'device': '/dev/mapper/vg-lv_name',
                'mount': '/mnt/special-path_123'
            }]
        }
        self.graph.add_node_data('node1', data)

        self.assertEqual(self.graph.nodes['node1'][0]['device'], '/dev/mapper/vg-lv_name')
        self.assertEqual(self.graph.nodes['node1'][0]['mount'], '/mnt/special-path_123')

    def test_empty_mount_point(self):
        """Test handling empty mount point"""
        data = {'fs': [{'device': '/dev/sda1', 'mount': ''}]}
        self.graph.add_node_data('node1', data)

        common = self.graph.get_common_storage()
        self.assertIn('', common)

    def test_duplicate_mount_same_node(self):
        """Test same mount point multiple times on same node"""
        data = {
            'fs': [
                {'device': '/dev/sda1', 'mount': '/data'},
                {'device': '/dev/sdb1', 'mount': '/data'}
            ]
        }
        self.graph.add_node_data('node1', data)

        # Both should be stored
        self.assertEqual(len(self.graph.nodes['node1']), 2)

    def test_very_long_values(self):
        """Test handling very long string values"""
        long_model = 'A' * 1000
        data = {'fs': [{'device': '/dev/sda1', 'model': long_model}]}

        self.graph.add_node_data('node1', data)
        self.assertEqual(self.graph.nodes['node1'][0]['model'], long_model)

    def test_unicode_in_values(self):
        """Test handling unicode characters"""
        data = {
            'fs': [{
                'device': '/dev/sda1',
                'mount': '/data/测试',
                'model': 'Samsung™ 970 EVO'
            }]
        }
        self.graph.add_node_data('node1', data)

        self.assertEqual(self.graph.nodes['node1'][0]['mount'], '/data/测试')


if __name__ == '__main__':
    unittest.main()
