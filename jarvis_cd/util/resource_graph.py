"""
Resource graph utilities for Jarvis.
Manages storage resource collection and analysis across nodes.
"""
import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
from .logger import logger


class ResourceGraph:
    """
    Manages storage resource information across multiple nodes.
    Collects, analyzes, and provides views of storage resources.
    """
    
    def __init__(self):
        """Initialize empty resource graph."""
        self.nodes: Dict[str, List[Dict[str, Any]]] = {}
        self.common_mounts: Dict[str, List[Dict[str, Any]]] = {}
        
    def add_node_data(self, hostname: str, resource_data: Dict[str, Any]):
        """
        Add resource data for a node.

        :param hostname: Hostname of the node
        :param resource_data: Resource data collected from the node
        """
        if hostname not in self.nodes:
            self.nodes[hostname] = []

        # Store filesystem data as dictionaries with hostname field
        for fs_data in resource_data.get('fs', []):
            device = fs_data.copy()
            device['hostname'] = hostname
            # Ensure all expected fields exist with defaults
            device.setdefault('device', '')
            device.setdefault('mount', '')
            device.setdefault('fs_type', 'unknown')
            device.setdefault('avail', '0B')
            device.setdefault('dev_type', 'unknown')
            device.setdefault('model', 'unknown')
            device.setdefault('parent', '')
            device.setdefault('uuid', '')
            device.setdefault('needs_root', False)
            device.setdefault('shared', False)
            device.setdefault('4k_randwrite_bw', 'unknown')
            device.setdefault('1m_seqwrite_bw', 'unknown')
            self.nodes[hostname].append(device)

        # Update common mounts analysis
        self._analyze_common_mounts()
        
    def _analyze_common_mounts(self):
        """Analyze which mount points are common across nodes.

        For multi-node clusters, mounts are common if they exist on multiple nodes.
        For single-node clusters, all mounts are considered common.
        """
        mount_counts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Group devices by mount point
        for hostname, devices in self.nodes.items():
            for device in devices:
                mount_counts[device['mount']].append(device)

        # Find mounts that exist on multiple nodes, or all mounts if single node
        self.common_mounts = {}
        total_nodes = len(self.nodes)

        for mount_point, devices in mount_counts.items():
            # Consider mount points common if:
            # 1. They exist on multiple nodes (len(devices) > 1), OR
            # 2. There's only one node in the cluster (all its mounts are "common")
            if len(devices) > 1 or total_nodes == 1:
                # Mark as shared if on multiple nodes or single node cluster
                for device in devices:
                    device['shared'] = True
                self.common_mounts[mount_point] = devices
                
    def get_common_storage(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get storage devices that are common across nodes (same mount point).

        For multi-node clusters: Returns mount points that exist on multiple nodes.
        For single-node clusters: Returns all mount points (all are considered common).

        :return: Dictionary mapping mount points to list of devices
        """
        return self.common_mounts.copy()

    def get_node_storage(self, hostname: str) -> List[Dict[str, Any]]:
        """
        Get storage devices for a specific node.

        :param hostname: Hostname to get storage for
        :return: List of storage devices
        """
        return self.nodes.get(hostname, [])
        
    def get_all_nodes(self) -> List[str]:
        """Get list of all node hostnames."""
        return list(self.nodes.keys())
        
    def get_storage_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of storage across all nodes.
        
        :return: Summary dictionary
        """
        total_devices = sum(len(devices) for devices in self.nodes.values())
        common_mounts = len(self.common_mounts)
        
        # Count device types
        dev_type_counts = defaultdict(int)
        fs_type_counts = defaultdict(int)

        for devices in self.nodes.values():
            for device in devices:
                dev_type_counts[device['dev_type']] += 1
                fs_type_counts[device['fs_type']] += 1
                
        return {
            'total_nodes': len(self.nodes),
            'total_devices': total_devices,
            'common_mount_points': common_mounts,
            'device_types': dict(dev_type_counts),
            'filesystem_types': dict(fs_type_counts)
        }
        
    def filter_by_type(self, dev_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter devices by device type (ssd, hdd, etc.).

        :param dev_type: Device type to filter by
        :return: Dictionary mapping hostnames to filtered devices
        """
        filtered = {}
        for hostname, devices in self.nodes.items():
            filtered_devices = [d for d in devices if d['dev_type'] == dev_type]
            if filtered_devices:
                filtered[hostname] = filtered_devices
        return filtered

    def filter_by_mount_pattern(self, pattern: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter devices by mount point pattern.

        :param pattern: Pattern to match in mount points
        :return: Dictionary mapping hostnames to filtered devices
        """
        filtered = {}
        for hostname, devices in self.nodes.items():
            filtered_devices = [d for d in devices if pattern in d['mount']]
            if filtered_devices:
                filtered[hostname] = filtered_devices
        return filtered
        
    def save_to_file(self, output_path: Path, format: str = 'yaml'):
        """
        Save resource graph to file.

        :param output_path: Path to save file
        :param format: Output format ('yaml' or 'json')
        """
        # Convert to serializable format - only store common mount points
        fs_data = []

        # Only store common mount points (accessible across nodes or single node)
        for mount_point, devices in self.common_mounts.items():
            # Use the first device as representative of the mount point
            if devices:
                device_dict = devices[0].copy()
                # Remove hostname-specific information
                device_dict.pop('hostname', None)
                fs_data.append(device_dict)

        data = {'fs': fs_data}

        # Save to file
        with open(output_path, 'w') as f:
            if format.lower() == 'json':
                json.dump(data, f, indent=2)
            else:  # Default to YAML
                yaml.dump(data, f, default_flow_style=False)

        logger.success(f"Resource graph saved to {output_path}")
        
    def load_from_file(self, input_path: Path):
        """
        Load resource graph from file.

        :param input_path: Path to load file from
        """
        with open(input_path, 'r') as f:
            if input_path.suffix.lower() == '.json':
                data = json.load(f)
            else:  # Default to YAML
                data = yaml.safe_load(f)

        # Clear existing data
        self.nodes = {}
        self.common_mounts = {}

        # Handle resource graph format with 'fs' section
        if 'fs' in data:
            # Determine hostname for resource graph files
            hostname = input_path.stem  # Use filename as hostname
            self.nodes[hostname] = []

            for device_data in data['fs']:
                # Expand environment variables in mount paths
                mount_path = device_data.get('mount', '')
                if mount_path:
                    mount_path = os.path.expandvars(mount_path)
                    device_data = device_data.copy()
                    device_data['mount'] = mount_path

                device = device_data.copy()
                device['hostname'] = hostname
                # Ensure all expected fields exist with defaults
                device.setdefault('device', '')
                device.setdefault('mount', '')
                device.setdefault('fs_type', 'unknown')
                device.setdefault('avail', '0B')
                device.setdefault('dev_type', 'unknown')
                device.setdefault('model', 'unknown')
                device.setdefault('parent', '')
                device.setdefault('uuid', '')
                device.setdefault('needs_root', False)
                device.setdefault('shared', False)
                device.setdefault('4k_randwrite_bw', 'unknown')
                device.setdefault('1m_seqwrite_bw', 'unknown')
                self.nodes[hostname].append(device)
        else:
            raise ValueError(f"Invalid resource graph format in {input_path}. Expected 'fs' section.")

        # Reanalyze common mounts
        self._analyze_common_mounts()

        logger.success(f"Resource graph loaded from {input_path}")
        
    def print_summary(self):
        """Print a summary of the resource graph."""
        summary = self.get_storage_summary()
        
        logger.info("=== Resource Graph Summary ===")
        logger.info(f"Total nodes: {summary['total_nodes']}")
        logger.info(f"Total storage devices: {summary['total_devices']}")
        logger.info(f"Common mount points: {summary['common_mount_points']}")
        
        if summary['device_types']:
            logger.info("Device types:")
            for dev_type, count in summary['device_types'].items():
                logger.info(f"  {dev_type}: {count}")
                
        if summary['filesystem_types']:
            logger.info("Filesystem types:")
            for fs_type, count in summary['filesystem_types'].items():
                logger.info(f"  {fs_type}: {count}")
                
    def print_common_storage(self):
        """Print information about common storage across nodes."""
        if not self.common_mounts:
            logger.warning("No common storage found across nodes")
            return

        total_nodes = len(self.nodes)
        if total_nodes == 1:
            logger.info("=== Available Storage (Single Node Cluster) ===")
        else:
            logger.info("=== Common Storage Across Nodes ===")

        for mount_point, devices in self.common_mounts.items():
            logger.info(f"\nMount point: {mount_point}")
            if total_nodes == 1:
                logger.info(f"Available on node: {devices[0]['hostname']}")
            else:
                logger.info(f"Available on {len(devices)} nodes:")

            for device in devices:
                perf_info = ""
                if device.get('4k_randwrite_bw', 'unknown') != 'unknown' and device.get('1m_seqwrite_bw', 'unknown') != 'unknown':
                    perf_info = f" [4K: {device.get('4k_randwrite_bw', 'unknown')}, 1M: {device.get('1m_seqwrite_bw', 'unknown')}]"

                logger.info(f"  {device['hostname']}: {device['device']} ({device['avail']}, {device['dev_type']}){perf_info}")
                
    def print_node_details(self, hostname: str):
        """
        Print detailed storage information for a specific node.

        :param hostname: Hostname to print details for
        """
        if hostname not in self.nodes:
            logger.error(f"Node {hostname} not found in resource graph")
            return

        devices = self.nodes[hostname]
        logger.info(f"=== Storage Details for {hostname} ===")
        logger.info(f"Total devices: {len(devices)}")

        for device in devices:
            logger.info(f"\nDevice: {device['device']}")
            logger.info(f"  Mount: {device['mount']}")
            logger.info(f"  Type: {device['dev_type']} ({device['fs_type']})")
            logger.info(f"  Available: {device['avail']}")
            logger.info(f"  Model: {device['model']}")
            logger.info(f"  Shared: {'Yes' if device['shared'] else 'No'}")

            if device.get('4k_randwrite_bw', 'unknown') != 'unknown':
                logger.info(f"  4K Random Write: {device.get('4k_randwrite_bw', 'unknown')}")
            if device.get('1m_seqwrite_bw', 'unknown') != 'unknown':
                logger.info(f"  1M Sequential Write: {device.get('1m_seqwrite_bw', 'unknown')}")