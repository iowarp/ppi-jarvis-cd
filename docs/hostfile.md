# Hostfile Class Documentation

## Overview

The `Hostfile` class provides a powerful and flexible way to manage sets of hostnames for distributed computing and cluster management. It supports parsing hostfile text with advanced pattern expansion, automatic IP resolution, and various host manipulation operations.

## Location

```python
from jarvis_cd.util.hostfile import Hostfile
```

## Core Features

- **Pattern Expansion**: Automatic expansion of bracket notation for host ranges
- **Multiple Input Sources**: Load from files, text, or manual lists  
- **IP Resolution**: Automatic hostname-to-IP mapping with optional disable
- **Host Manipulation**: Subset, copy, enumerate, and string operations
- **Local Detection**: Automatic detection of localhost-only configurations

## Constructor

```python
def __init__(self, path: Optional[str] = None, hosts: Optional[List[str]] = None, 
             hosts_ip: Optional[List[str]] = None, text: Optional[str] = None, 
             find_ips: bool = True, load_path: bool = True):
    """
    Constructor. Parse hostfile or store existing host list.

    :param path: The path to the hostfile
    :param hosts: a list of strings representing all hostnames
    :param hosts_ip: a list of strings representing all host IPs
    :param text: Text of a hostfile
    :param find_ips: Whether to construct host_ip and all_host_ip fields
    :param load_path: whether or not path should exist and be read from on init
    """
```

**Parameters**:
- `path` (str, optional): Path to hostfile on filesystem
- `hosts` (List[str], optional): Manual list of hostnames
- `hosts_ip` (List[str], optional): Manual list of IP addresses
- `text` (str, optional): Raw hostfile text content
- `find_ips` (bool): Enable automatic IP resolution (default: True)
- `load_path` (bool): Whether to read from path during initialization (default: True)

**Behavior**:
- If no parameters provided: Creates localhost-only hostfile
- If `hosts` provided: Uses manual host list
- If `path` provided and `load_path=True`: Loads from filesystem
- If `text` provided: Parses hostfile content
- If `find_ips=True`: Automatically resolves hostnames to IPs

## Attributes

After initialization, the following attributes are available:

```python
hostfile.path          # str: Path to hostfile (if loaded from file)
hostfile.hosts         # List[str]: List of hostnames
hostfile.hosts_ip      # List[str]: List of IP addresses
hostfile.find_ips      # bool: Whether IP resolution is enabled
```

## Pattern Expansion

The Hostfile class supports sophisticated pattern expansion using bracket notation:

### Numeric Ranges
```python
# Input: "ares-comp-[02-04]"
# Output: ["ares-comp-02", "ares-comp-03", "ares-comp-04"]

# Zero-padding preserved
# Input: "node-[001-003]"  
# Output: ["node-001", "node-002", "node-003"]
```

### Alphabetic Ranges
```python
# Lowercase: "server-[a-c]"
# Output: ["server-a", "server-b", "server-c"]

# Uppercase: "server-[A-C]"
# Output: ["server-A", "server-B", "server-C"]
```

### Lists and Complex Patterns
```python
# List notation: "compute-[1,3,5]"
# Output: ["compute-1", "compute-3", "compute-5"]

# Mixed ranges and lists: "ares-comp-[05-09,11,12-14]-40g"
# Output: ["ares-comp-05-40g", "ares-comp-06-40g", ..., "ares-comp-14-40g"]
```

### Multi-line Hostfiles
```
ares-comp-01
ares-comp-[02-04]
ares-comp-[05-09,11,12-14]-40g
```

## Core Methods

### subset()

```python
def subset(self, count: int, path: Optional[str] = None) -> 'Hostfile':
    """
    Return a subset of the first 'count' hosts.
    
    :param count: Number of hosts to include
    :param path: Optional path for the new hostfile
    :return: New Hostfile with subset of hosts
    """
```

**Example**:
```python
hostfile = Hostfile(text="node-[01-10]", find_ips=False)
subset = hostfile.subset(3)  # First 3 hosts
print(subset.hosts)  # ['node-01', 'node-02', 'node-03']
```

### copy()

```python
def copy(self) -> 'Hostfile':
    """
    Return a complete copy of this hostfile.
    
    :return: New Hostfile with same hosts and settings
    """
```

**Example**:
```python
original = Hostfile(hosts=['host1', 'host2'])
copy = original.copy()
# copy.hosts is a separate list with same content
```

### is_local()

```python
def is_local(self) -> bool:
    """
    Whether this file contains only 'localhost'.
    
    :return: True if localhost-only, False otherwise
    """
```

**Example**:
```python
localhost_file = Hostfile()  # Default constructor
print(localhost_file.is_local())  # True

multi_host = Hostfile(hosts=['host1', 'host2'])
print(multi_host.is_local())  # False
```

### save()

```python
def save(self, path: str) -> 'Hostfile':
    """
    Save hostfile to filesystem.
    
    :param path: File path to save to
    :return: Self for method chaining
    """
```

**Example**:
```python
hostfile = Hostfile(text="node-[01-03]")
hostfile.save('/tmp/my_hostfile.txt')
```

### list()

```python
def list(self) -> List['Hostfile']:
    """
    Return a list of single-host Hostfile objects.
    
    :return: List of Hostfile objects, one per host
    """
```

**Example**:
```python
hostfile = Hostfile(hosts=['host1', 'host2'])
host_list = hostfile.list()
print(len(host_list))        # 2
print(host_list[0].hosts)    # ['host1']
print(host_list[1].hosts)    # ['host2']
```

### enumerate()

```python
def enumerate(self):
    """
    Return enumerated list of single-host Hostfile objects.
    
    :return: Generator of (index, Hostfile) tuples
    """
```

**Example**:
```python
hostfile = Hostfile(hosts=['host1', 'host2'])
for i, single_host in hostfile.enumerate():
    print(f"{i}: {single_host.hosts[0]}")
# Output:
# 0: host1
# 1: host2
```

### host_str()

```python
def host_str(self, sep: str = ',') -> str:
    """
    Return hosts as a separated string.
    
    :param sep: Separator string (default: comma)
    :return: Hosts joined by separator
    """
```

**Example**:
```python
hostfile = Hostfile(hosts=['host1', 'host2', 'host3'])
print(hostfile.host_str())      # "host1,host2,host3"
print(hostfile.host_str('|'))   # "host1|host2|host3"
```

### ip_str()

```python
def ip_str(self, sep: str = ',') -> str:
    """
    Return host IPs as a separated string.
    
    :param sep: Separator string (default: comma)
    :return: IPs joined by separator
    """
```

**Example**:
```python
hostfile = Hostfile(hosts=['localhost'])
print(hostfile.ip_str())  # "127.0.0.1" (or similar)
```

## Built-in Methods

### Length and Indexing

```python
len(hostfile)           # Number of hosts
hostfile[0]             # First hostname
hostfile[-1]            # Last hostname
hostfile[1:3]           # Slice of hostnames
```

### Iteration

```python
for hostname in hostfile:
    print(hostname)

# Or get all as list
all_hosts = list(hostfile)
```

### String Representation

```python
str(hostfile)           # "Hostfile(3 hosts: host1,host2,host3)"
repr(hostfile)          # "Hostfile(hosts=['host1', 'host2'], hosts_ip=[...])"
```

## Usage Examples

### Default Localhost

```python
# Create localhost hostfile
hostfile = Hostfile()
print(hostfile.hosts)      # ['localhost']
print(hostfile.is_local()) # True
```

### From File

```python
# Load from filesystem
hostfile = Hostfile(path='/etc/hostfile.txt')
print(f"Loaded {len(hostfile)} hosts")
```

### From Text Pattern

```python
# Parse text with pattern expansion
text = """
compute-[01-05]
gpu-[a-d]
storage-[1,3,5]
"""
hostfile = Hostfile(text=text, find_ips=False)
print(hostfile.hosts)
# ['compute-01', 'compute-02', ..., 'gpu-a', 'gpu-b', ..., 'storage-1', ...]
```

### Manual Host List

```python
# Create from manual list
hosts = ['node1.cluster.edu', 'node2.cluster.edu', 'node3.cluster.edu']
hostfile = Hostfile(hosts=hosts, find_ips=False)
```

### Disable IP Resolution

```python
# For performance when IPs not needed
hostfile = Hostfile(text="node-[001-100]", find_ips=False)
print(hostfile.hosts_ip)  # []
```

### Host Manipulation

```python
# Create large hostfile
hostfile = Hostfile(text="node-[01-20]", find_ips=False)

# Get subset for testing
test_hosts = hostfile.subset(3)
print(test_hosts.hosts)  # ['node-01', 'node-02', 'node-03']

# Create backup copy
backup = hostfile.copy()

# Get comma-separated string for external tools
host_string = hostfile.host_str()
```

### File Operations

```python
# Load, modify, and save
hostfile = Hostfile(path='input_hosts.txt')
subset = hostfile.subset(10)
subset.save('first_10_hosts.txt')
```

### Working with Individual Hosts

```python
hostfile = Hostfile(text="node-[01-03]", find_ips=False)

# Process each host individually
for i, single_host in hostfile.enumerate():
    print(f"Processing host {i}: {single_host.hosts[0]}")
    # single_host is a Hostfile with one host
    
# Or get list of single-host objects
host_objects = hostfile.list()
first_host = host_objects[0]  # Hostfile with just first host
```

## IP Resolution

When `find_ips=True` (default), the class automatically resolves hostnames:

```python
hostfile = Hostfile(hosts=['localhost', 'google.com'])
print(hostfile.hosts)     # ['localhost', 'google.com'] 
print(hostfile.hosts_ip)  # ['127.0.0.1', '142.250.191.14'] (example)
```

**Notes**:
- Resolution happens during initialization
- Failed resolutions use hostname as IP
- Disable with `find_ips=False` for performance
- `localhost` is always resolved correctly

## Error Handling

```python
# File not found
try:
    hostfile = Hostfile(path='/nonexistent/file.txt')
except FileNotFoundError:
    print("Hostfile not found")

# Invalid patterns are treated as literals
hostfile = Hostfile(text="invalid-[pattern", find_ips=False)
print(hostfile.hosts)  # ['invalid-[pattern']
```

## Performance Considerations

1. **IP Resolution**: Disable with `find_ips=False` for large host lists
2. **Pattern Complexity**: Complex patterns with large ranges may take time to expand
3. **File Loading**: Use `load_path=False` when creating derived hostfiles

## Testing

Comprehensive unit tests are available at `test/unit/test_hostfile.py` covering:
- Pattern expansion (numeric, alphabetic, mixed)
- File loading and saving
- IP resolution
- Host manipulation methods
- Edge cases and error conditions
- Zero-padding preservation
- Multi-line hostfiles

## Integration Examples

### With ArgParse

```python
class MyAppArgParse(ArgParse):
    def define_options(self):
        self.add_menu('')
        self.add_cmd('run')
        self.add_args([
            {
                'name': 'hostfile',
                'msg': 'Path to hostfile',
                'type': str,
                'required': True
            },
            {
                'name': 'node_count',
                'msg': 'Number of nodes to use',
                'type': int,
                'default': None
            }
        ])
    
    def run(self):
        # Load hostfile
        hostfile = Hostfile(path=self.kwargs['hostfile'])
        
        # Use subset if specified
        if self.kwargs['node_count']:
            hostfile = hostfile.subset(self.kwargs['node_count'])
            
        print(f"Running on {len(hostfile)} hosts: {hostfile.host_str()}")
```

### Cluster Management

```python
def deploy_to_cluster(app_path, hostfile_path):
    """Deploy application to cluster hosts"""
    hostfile = Hostfile(path=hostfile_path)
    
    if hostfile.is_local():
        print("Running locally")
        run_local(app_path)
    else:
        print(f"Deploying to {len(hostfile)} hosts")
        for i, single_host in hostfile.enumerate():
            hostname = single_host.hosts[0]
            ip = single_host.hosts_ip[0]
            print(f"Deploying to {hostname} ({ip})")
            deploy_to_host(app_path, hostname)
```

## Best Practices

1. **Use `find_ips=False`** for large host lists when IPs aren't needed
2. **Validate hostfile existence** before loading from paths
3. **Use `subset()`** for testing with smaller host counts
4. **Save derived hostfiles** for reuse in complex workflows
5. **Check `is_local()`** to handle single-machine vs. distributed cases
6. **Use pattern expansion** to reduce hostfile maintenance overhead
7. **Test pattern expansion** with small examples before large deployments