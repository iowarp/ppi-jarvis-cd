# Jarvis CD Utility Classes Documentation

This documentation describes the utility classes implemented for the Jarvis CD project. These classes provide essential functionality for command-line argument parsing and host management in distributed computing environments.

## Overview

The `jarvis_cd.util` package contains two main utility classes:

1. **ArgParse** - Custom command-line argument parser with advanced features
2. **Hostfile** - Host management with pattern expansion and IP resolution

Both classes are designed to work together to provide a comprehensive foundation for building command-line tools and distributed computing applications.

## Quick Start

### Basic Imports

```python
from jarvis_cd.util.argparse import ArgParse
from jarvis_cd.util.hostfile import Hostfile
```

### Simple Example

```python
# Create a hostfile
hostfile = Hostfile(text="node-[01-05]", find_ips=False)
print(f"Hosts: {hostfile.host_str()}")  # node-01,node-02,node-03,node-04,node-05

# Create an argument parser
class MyParser(ArgParse):
    def define_options(self):
        self.add_menu('')
        self.add_cmd('run')
        self.add_args([
            {'name': 'nodes', 'type': int, 'required': True, 'pos': True}
        ])
    
    def run(self):
        print(f"Running with {self.kwargs['nodes']} nodes")

parser = MyParser()
parser.define_options()
parser.parse(['run', '4'])  # Running with 4 nodes
```

## Class Documentation

### [ArgParse Class](./argparse.md)

A sophisticated command-line argument parser supporting:
- **Menu/Command Structure**: Hierarchical organization of commands
- **Argument Types**: Positional, keyword, list, and remainder arguments  
- **Advanced Features**: Command aliases, argument ranking, type casting
- **Custom Handlers**: Automatic method dispatch for commands

**Key Features**:
- Complex argument structures with classes and ranking
- List arguments with set and append modes
- Automatic type conversion (str, int, bool, list)
- Command aliases and flexible syntax
- Comprehensive error handling

**Use Cases**:
- Building CLI applications with subcommands
- Scientific computing parameter management
- Distributed computing job configuration
- Complex workflow orchestration

### [Hostfile Class](./hostfile.md)

A powerful host management system supporting:
- **Pattern Expansion**: Bracket notation for host ranges (`node-[01-10]`)
- **Multiple Sources**: Files, text, manual lists
- **IP Resolution**: Automatic hostname-to-IP mapping
- **Host Operations**: Subset, copy, enumerate, string formatting

**Key Features**:
- Numeric and alphabetic range expansion
- Zero-padding preservation in numeric ranges
- Multi-line hostfile support
- Local vs. distributed detection
- Performance optimizations for large host sets

**Use Cases**:
- Cluster job submission
- Distributed computing node management
- Network administration tools
- Load balancing configuration

## Integration Patterns

### CLI Application with Host Management

```python
class ClusterApp(ArgParse):
    def define_options(self):
        self.add_menu('')
        self.add_cmd('deploy', aliases=['d'])
        self.add_args([
            {
                'name': 'hostfile',
                'msg': 'Path to hostfile',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'app_path',
                'msg': 'Application to deploy',
                'type': str,
                'required': True,
                'pos': True
            },
            {
                'name': 'nodes',
                'msg': 'Number of nodes to use',
                'type': int,
                'default': None
            },
            {
                'name': 'dry_run',
                'msg': 'Perform dry run',
                'type': bool,
                'default': False
            }
        ])
    
    def deploy(self):
        # Load hostfile
        hostfile = Hostfile(path=self.kwargs['hostfile'])
        
        # Use subset if specified
        if self.kwargs['nodes']:
            hostfile = hostfile.subset(self.kwargs['nodes'])
        
        if self.kwargs['dry_run']:
            print(f"Would deploy {self.kwargs['app_path']} to:")
            for hostname in hostfile:
                print(f"  - {hostname}")
        else:
            print(f"Deploying to {len(hostfile)} hosts...")
            self._deploy_to_hosts(hostfile, self.kwargs['app_path'])

# Usage: python app.py deploy /etc/hostfile.txt /path/to/app --nodes=5 --dry_run=true
```

### Batch Job Processor

```python
class BatchProcessor(ArgParse):
    def define_options(self):
        self.add_menu('batch', msg="Batch processing commands")
        
        self.add_cmd('batch submit')
        self.add_args([
            {
                'name': 'job_script',
                'type': str,
                'required': True,
                'pos': True,
                'class': 'files',
                'rank': 0
            },
            {
                'name': 'nodes',
                'msg': 'Node specifications',
                'type': list,
                'aliases': ['n'],
                'args': [
                    {'name': 'pattern', 'type': str},
                    {'name': 'count', 'type': int}
                ]
            }
        ])
    
    def batch_submit(self):
        # Process node specifications
        all_hosts = []
        for node_spec in self.kwargs.get('nodes', []):
            pattern = node_spec['pattern']
            count = node_spec['count']
            
            hostfile = Hostfile(text=pattern, find_ips=False)
            subset = hostfile.subset(count)
            all_hosts.extend(subset.hosts)
        
        print(f"Submitting job to hosts: {','.join(all_hosts)}")
        self._submit_job(self.kwargs['job_script'], all_hosts)

# Usage: python batch.py batch submit job.sh --n "(node-[01-10], 3)" --n "(gpu-[a-d], 2)"
```

## Testing

Both classes include comprehensive test suites:

- **ArgParse Tests**: `test/unit/test_argparse.py` (13 test cases)
- **Hostfile Tests**: `test/unit/test_hostfile.py` (30 test cases)

Run tests with:
```bash
python -m pytest test/unit/ -v
```

## Architecture Notes

### Design Principles

1. **Flexibility**: Support multiple input/output formats and use cases
2. **Performance**: Efficient parsing and processing for large datasets
3. **Extensibility**: Easy to subclass and extend for specific needs
4. **Robustness**: Comprehensive error handling and edge case management
5. **Testability**: Well-tested with extensive unit test coverage

### Class Relationships

```
ArgParse
├── User-defined parsers (inherit from ArgParse)
├── Command handlers (methods in subclasses)
└── Argument specifications (dictionaries)

Hostfile
├── Pattern expansion engine
├── IP resolution system
└── Host manipulation operations
```

### Dependencies

- **Standard Library**: `socket`, `re`, `os`, `ast`, `typing`
- **Testing**: `unittest`, `tempfile`
- **No External Dependencies**: Both classes use only Python standard library

## File Structure

```
jarvis_cd/
├── util/
│   ├── __init__.py
│   ├── argparse.py       # ArgParse class implementation
│   └── hostfile.py       # Hostfile class implementation
├── test/
│   └── unit/
│       ├── test_argparse.py   # ArgParse unit tests
│       └── test_hostfile.py   # Hostfile unit tests
└── docs/
    ├── README.md         # This overview document
    ├── argparse.md       # Detailed ArgParse documentation
    └── hostfile.md       # Detailed Hostfile documentation
```

## Best Practices

### For ArgParse

1. **Define clear command hierarchies** with logical menu organization
2. **Use argument classes and ranks** for intuitive positional ordering
3. **Provide meaningful aliases** for frequently used commands
4. **Implement robust error handling** in command methods
5. **Test complex argument combinations** thoroughly

### For Hostfile

1. **Use pattern expansion** to minimize hostfile maintenance
2. **Disable IP resolution** for large host lists when not needed
3. **Test patterns** with small examples before large deployments
4. **Handle file not found** gracefully in applications
5. **Use `is_local()`** to detect single-machine vs. distributed scenarios

### For Integration

1. **Combine both classes** for comprehensive CLI applications
2. **Validate hostfile patterns** before expensive operations
3. **Use subset operations** for testing and development
4. **Cache hostfile objects** for repeated use
5. **Document command structures** clearly for users

## Future Extensions

Potential areas for enhancement:

1. **ArgParse**: Configuration file support, command completion, help generation
2. **Hostfile**: SSH key management, health checking, load balancing hints
3. **Integration**: Plugin system, workflow orchestration, monitoring hooks

## Contributing

When extending these classes:

1. **Maintain backward compatibility** in public APIs
2. **Add comprehensive tests** for new functionality
3. **Update documentation** with examples and use cases
4. **Follow existing code style** and patterns
5. **Consider performance impact** of changes

---

For detailed API documentation and examples, see the individual class documentation:
- [ArgParse Class Documentation](./argparse.md)
- [Hostfile Class Documentation](./hostfile.md)