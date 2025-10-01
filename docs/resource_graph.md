# Jarvis-CD Resource Graph

The Resource Graph is a comprehensive system for discovering, analyzing, and querying storage resources across compute clusters. It collects detailed information about storage devices, filesystems, and performance characteristics from all nodes in the cluster.

## Table of Contents

1. [Overview](#overview)
2. [Building the Resource Graph](#building-the-resource-graph)
3. [Querying Storage Devices](#querying-storage-devices)
4. [Resource Graph CLI Commands](#resource-graph-cli-commands)
5. [Programmatic API](#programmatic-api)
6. [Storage Device Information](#storage-device-information)
7. [Performance Benchmarking](#performance-benchmarking)
8. [Common Use Cases](#common-use-cases)
9. [File Formats](#file-formats)

## Overview

The Resource Graph provides:

- **Automatic Discovery**: Identifies all accessible storage devices across cluster nodes
- **Performance Metrics**: Benchmarks storage performance (4K random write, 1M sequential write)
- **Common Storage Analysis**: Finds storage mount points available across multiple nodes (or all mounts for single-node clusters)
- **Device Classification**: Categorizes storage by type (SSD, HDD, etc.) and filesystem
- **Programmatic Access**: Query storage resources from packages and applications
- **Persistent Storage**: Save and load resource graphs for reuse

### Key Components

- **ResourceGraphManager**: Coordinates resource collection across the cluster
- **ResourceGraph**: Manages storage resource data and provides query methods
- **CLI Commands**: User-friendly commands for building and querying the resource graph

## Building the Resource Graph

### Prerequisites

1. **Set Hostfile**: Configure the cluster nodes to scan
2. **Network Access**: Ensure SSH connectivity to all nodes
3. **Storage Access**: Verify user permissions on target storage devices

### Basic Usage

```bash
# Set the hostfile first
jarvis hostfile set /path/to/hostfile

# Build resource graph with performance benchmarking
jarvis rg build

# Build without benchmarking (faster)
jarvis rg build +no_benchmark

# Build with custom benchmark duration
jarvis rg build duration=60
```

### Hostfile Format

```
node1.cluster.local
node2.cluster.local  
node3.cluster.local
192.168.1.100
localhost
```

### Collection Process

1. **Parallel Collection**: Resource data is collected from all nodes simultaneously
2. **Storage Discovery**: Identifies mounted filesystems accessible to the current user
3. **Device Analysis**: Determines device type, model, and capacity
4. **Performance Benchmarking**: Measures I/O performance (optional)
5. **Common Storage Analysis**: Identifies shared mount points across nodes
6. **Persistent Storage**: Saves results to `~/.ppi-jarvis/resource_graph.yaml`

## Querying Storage Devices

### Get All Storage Devices

```python
from jarvis_cd.core.resource_graph import ResourceGraphManager
from jarvis_cd.core.config import JarvisConfig

# Initialize (automatically loads resource graph if it exists)
jarvis_config = JarvisConfig()
rg_manager = ResourceGraphManager(jarvis_config)

# Or explicitly load resource graph from a specific file
rg_manager.load('/path/to/resource_graph.yaml')

# Get all nodes
nodes = rg_manager.resource_graph.get_all_nodes()
print(f"Cluster nodes: {nodes}")

# Get storage for specific node
storage_devices = rg_manager.resource_graph.get_node_storage('node1')
for device in storage_devices:
    print(f"{device['mount']}: {device['avail']} ({device['dev_type']})")
```

### Filter by Device Type

```python
# Get only SSD devices across all nodes
ssd_devices = rg_manager.resource_graph.filter_by_type('ssd')
for hostname, devices in ssd_devices.items():
    print(f"\n{hostname} SSDs:")
    for device in devices:
        print(f"  {device['mount']}: {device['avail']}")

# Get HDD devices
hdd_devices = rg_manager.resource_graph.filter_by_type('hdd')
```

### Get Common Storage

```python
# Find storage mount points available on multiple nodes
# Note: For single-node clusters, all mount points are considered "common"
common_storage = rg_manager.resource_graph.get_common_storage()
for mount_point, devices in common_storage.items():
    print(f"\nMount {mount_point} available on {len(devices)} nodes:")
    for device in devices:
        print(f"  {device['hostname']}: {device['avail']}")
```

### Filter by Mount Pattern

```python
# Find all /tmp or temporary storage
tmp_storage = rg_manager.resource_graph.filter_by_mount_pattern('/tmp')

# Find home directories  
home_storage = rg_manager.resource_graph.filter_by_mount_pattern('/home')

# Find specific mount points
scratch_storage = rg_manager.resource_graph.filter_by_mount_pattern('/scratch')
```

## Resource Graph CLI Commands

### Build Commands

```bash
# Build complete resource graph
jarvis rg build

# Build without performance benchmarking  
jarvis rg build +no_benchmark

# Build with custom benchmark duration
jarvis rg build duration=30
```

### Query Commands

```bash
# Show resource graph summary
jarvis rg show

# List all nodes in resource graph
jarvis rg nodes

# Show detailed information for specific node
jarvis rg node hostname1

# Filter storage devices by type
jarvis rg filter ssd
jarvis rg filter hdd
jarvis rg filter nvme

# Show resource graph file path (output only the path)
jarvis rg path
```

### Management Commands

```bash
# Load resource graph from custom file
jarvis rg load /path/to/custom_resource_graph.yaml

# Show path to current resource graph file (prints only the path)
jarvis rg path

# Use in shell command substitution
cd $(dirname $(jarvis rg path))  # Navigate to resource graph directory
ls -la $(jarvis rg path)         # List resource graph file details

# Resource graph is automatically saved to ~/.ppi-jarvis/resource_graph.yaml
# after building
```

## Programmatic API

### ResourceGraph Class

```python
from jarvis_cd.util.resource_graph import ResourceGraph

# Create and populate resource graph
rg = ResourceGraph()

# Add node data (typically done during collection)
node_data = {
    'fs': [
        {
            'device': '/dev/sda1',
            'mount': '/home',
            'fs_type': 'ext4', 
            'avail': '100GB',
            'dev_type': 'ssd',
            'model': 'Samsung SSD 970',
            '4k_randwrite_bw': '50MB/s',
            '1m_seqwrite_bw': '500MB/s'
        }
    ]
}
rg.add_node_data('node1', node_data)
```

### Query Methods

```python
# Get all nodes
nodes = rg.get_all_nodes()

# Get storage for specific node
devices = rg.get_node_storage('node1')

# Get summary statistics
summary = rg.get_storage_summary()
print(f"Total devices: {summary['total_devices']}")
print(f"Device types: {summary['device_types']}")

# Filter by type
ssd_devices = rg.filter_by_type('ssd')
hdd_devices = rg.filter_by_type('hdd')

# Filter by mount pattern
tmp_mounts = rg.filter_by_mount_pattern('/tmp')

# Get common storage across nodes
common = rg.get_common_storage()
```

### Device Dictionary Structure

Storage devices are represented as dictionaries with the following fields:

```python
device = devices[0]  # Get first device (dict)

# Basic properties
print(f"Device: {device['device']}")           # /dev/sda1
print(f"Mount: {device['mount']}")             # /home
print(f"Type: {device['dev_type']}")           # ssd
print(f"Filesystem: {device['fs_type']}")      # ext4
print(f"Available: {device['avail']}")         # 100GB
print(f"Hostname: {device['hostname']}")       # node1

# Optional properties (use .get() with defaults)
print(f"Model: {device.get('model', 'unknown')}")        # Samsung SSD 970
print(f"Shared: {device.get('shared', False)}")          # True if on multiple nodes

# Performance metrics (optional, present if benchmarking was performed)
print(f"4K Random Write: {device.get('4k_randwrite_bw', 'unknown')}")  # 50MB/s
print(f"1M Sequential: {device.get('1m_seqwrite_bw', 'unknown')}")     # 500MB/s

# System properties (optional)
print(f"UUID: {device.get('uuid', 'unknown')}")               # Filesystem UUID
print(f"Parent: {device.get('parent', 'unknown')}")           # Parent device
print(f"Needs Root: {device.get('needs_root', False)}")       # Requires root access
```

## Storage Device Information

### Device Detection

The resource graph automatically detects:

- **Physical Devices**: `/dev/sda`, `/dev/nvme0n1`, etc.
- **Mount Points**: `/`, `/home`, `/tmp`, `/scratch`, etc.
- **Filesystem Types**: `ext4`, `xfs`, `btrfs`, `tmpfs`, etc.
- **Device Types**: `ssd`, `hdd`, `nvme`, `unknown`
- **Access Permissions**: Whether current user can write to the mount

### Device Classification

Storage devices are classified by type:

- **`ssd`**: Solid State Drives
- **`hdd`**: Hard Disk Drives  
- **`nvme`**: NVMe devices
- **`unknown`**: Unidentified device types

### Capacity Information

Available space is reported in human-readable format:
- `1.2TB` - Terabytes
- `500GB` - Gigabytes
- `10MB` - Megabytes

## Performance Benchmarking

### Benchmark Types

The resource graph can measure storage performance using:

1. **4K Random Write**: Small random I/O performance
2. **1M Sequential Write**: Large sequential I/O performance

### Benchmark Configuration

```bash
# Enable benchmarking (default)
jarvis rg build

# Disable benchmarking for faster collection
jarvis rg build +no_benchmark

# Custom benchmark duration (default: 25 seconds)
jarvis rg build duration=60
```

### Performance Metrics

```python
# Access performance data
for device in devices:
    if device.get('4k_randwrite_bw', 'unknown') != 'unknown':
        print(f"4K Random Write: {device['4k_randwrite_bw']}")
    if device.get('1m_seqwrite_bw', 'unknown') != 'unknown':
        print(f"1M Sequential: {device['1m_seqwrite_bw']}")
```

### Performance Considerations

- **Benchmarking Time**: Longer durations provide more accurate results
- **I/O Impact**: Benchmarks perform actual write operations
- **Permissions**: Some benchmarks may require specific mount point access
- **Concurrent Access**: Multiple nodes benchmark simultaneously

## Common Use Cases

### 1. Find High-Performance Storage

```python
# Find SSDs with good performance across the cluster
ssd_devices = rg.filter_by_type('ssd')
high_perf_storage = {}

for hostname, devices in ssd_devices.items():
    good_devices = []
    for device in devices:
        # Parse bandwidth (simplified)
        seq_bw = device.get('1m_seqwrite_bw', '')
        if seq_bw and 'GB/s' in seq_bw:
            good_devices.append(device)
    if good_devices:
        high_perf_storage[hostname] = good_devices

print(f"High-performance storage found on {len(high_perf_storage)} nodes")
```

### 2. Find Common Scratch Space

```python
# Get scratch directories available on all nodes
common_storage = rg.get_common_storage()
scratch_spaces = {mount: devices for mount, devices in common_storage.items() 
                  if '/scratch' in mount or '/tmp' in mount}

print("Available scratch spaces:")
for mount, devices in scratch_spaces.items():
    print(f"  {mount}: available on {len(devices)} nodes")
```

### 3. Package Storage Selection

```python
# In a package's _configure method
class MyApp(Application):
    def _configure(self, **kwargs):
        # Configuration automatically updated

        # Get resource graph (automatically loaded on init)
        from jarvis_cd.core.resource_graph import ResourceGraphManager
        rg_manager = ResourceGraphManager(self.jarvis.jarvis_config)

        # Find fast storage for output
        ssd_storage = rg_manager.resource_graph.filter_by_type('ssd')
        if ssd_storage:
            # Use first available SSD
            hostname, devices = next(iter(ssd_storage.items()))
            output_dir = devices[0]['mount'] + '/my_app_output'
            self.setenv('OUTPUT_DIR', output_dir)
            print(f"Using fast storage: {output_dir}")
```

### 4. Storage Capacity Planning

```python
# Calculate total available storage by type
summary = rg.get_storage_summary()
print(f"Cluster storage summary:")
print(f"  Total devices: {summary['total_devices']}")
print(f"  Device types: {summary['device_types']}")

# Find nodes with large storage
large_storage_nodes = {}
for hostname in rg.get_all_nodes():
    devices = rg.get_node_storage(hostname)
    for device in devices:
        # Parse capacity (simplified - actual parsing would be more robust)
        if 'TB' in device['avail']:
            if hostname not in large_storage_nodes:
                large_storage_nodes[hostname] = []
            large_storage_nodes[hostname].append(device)

print(f"Nodes with large storage: {list(large_storage_nodes.keys())}")
```

### 5. Validate Storage Access

```python
# Check that required storage is available
required_mounts = ['/scratch', '/tmp', '/home']
available_mounts = set()

for hostname in rg.get_all_nodes():
    devices = rg.get_node_storage(hostname)
    node_mounts = {device['mount'] for device in devices}
    available_mounts.update(node_mounts)

missing_mounts = set(required_mounts) - available_mounts
if missing_mounts:
    print(f"Warning: Missing required storage: {missing_mounts}")
else:
    print("All required storage mounts available")
```

## File Formats

### YAML Format (Default)

```yaml
nodes:
  node1:
    - device: /dev/sda1
      mount: /home
      fs_type: ext4
      avail: 100GB
      dev_type: ssd
      model: Samsung SSD 970
      shared: true
      4k_randwrite_bw: 50MB/s
      1m_seqwrite_bw: 500MB/s
      
common_mounts:
  /home:
    - device: /dev/sda1
      mount: /home
      # ... device details
      
summary:
  total_nodes: 3
  total_devices: 12
  common_mount_points: 2
  device_types:
    ssd: 8
    hdd: 4
  filesystem_types:
    ext4: 10
    xfs: 2
```

### JSON Format

```python
# Save as JSON
rg.save_to_file(Path('resource_graph.json'), format='json')

# Load JSON
rg.load_from_file(Path('resource_graph.json'))
```

### Loading Custom Resource Graphs

```bash
# Load from custom location
jarvis rg load /shared/cluster_storage.yaml

# Default location (automatically loaded)
# ~/.ppi-jarvis/resource_graph.yaml
```

### Shell Integration

The `jarvis rg path` command outputs only the file path, making it perfect for shell command substitution:

```bash
# Navigate to the resource graph directory
cd $(dirname $(jarvis rg path))

# Edit the resource graph file
vim $(jarvis rg path)

# Copy resource graph to another location
cp $(jarvis rg path) /backup/

# Check file details
ls -la $(jarvis rg path)

# View resource graph contents
cat $(jarvis rg path)

# Backup resource graph with timestamp
cp $(jarvis rg path) $(jarvis rg path).backup.$(date +%Y%m%d)
```

**Error Handling**: If no resource graph exists, the command will exit with status code 1 and print error messages to stderr, ensuring command substitution fails gracefully.

### Integration with Packages

```python
# Access resource graph in package code
class StorageAwareApp(Application):
    def _configure(self, **kwargs):
        # Configuration automatically updated

        # Get resource graph (automatically loaded on init if it exists)
        rg_manager = ResourceGraphManager(self.jarvis.jarvis_config)
        if not rg_manager.resource_graph.get_all_nodes():
            print("No resource graph found. Run 'jarvis rg build' first.")
            return

        # Find optimal storage for this application
        storage_choice = self._select_storage(rg_manager.resource_graph)
        self.setenv('APP_STORAGE_PATH', storage_choice)

    def _select_storage(self, rg):
        """Select optimal storage based on requirements"""
        # Example: prefer SSDs for output
        ssd_storage = rg.filter_by_type('ssd')
        if ssd_storage:
            hostname, devices = next(iter(ssd_storage.items()))
            return devices[0]['mount'] + '/app_output'

        # Fallback to any available storage
        all_nodes = rg.get_all_nodes()
        if all_nodes:
            devices = rg.get_node_storage(all_nodes[0])
            if devices:
                return devices[0]['mount'] + '/app_output'

        return '/tmp/app_output'  # Final fallback
```

The Resource Graph provides a powerful foundation for storage-aware application deployment and performance optimization across heterogeneous clusters.