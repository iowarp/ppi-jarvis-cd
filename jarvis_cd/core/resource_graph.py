"""
Resource graph management for Jarvis.
Coordinates resource collection across nodes and provides analysis capabilities.
"""
import json
import sys
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from jarvis_cd.core.config import Jarvis
from jarvis_cd.util.resource_graph import ResourceGraph
from jarvis_cd.util.logger import logger
from jarvis_cd.shell import ResourceGraphExec, PsshExecInfo, LocalExec, LocalExecInfo


class ResourceGraphManager:
    """
    Manages resource graph collection and analysis across the Jarvis cluster.
    """
    
    def __init__(self):
        """
        Initialize resource graph manager.
        Gets Jarvis singleton internally.
        """
        self.jarvis = Jarvis.get_instance()
        self.resource_graph = ResourceGraph()

        # Try to load existing resource graph if available
        default_path = Path.home() / '.ppi-jarvis' / 'resource_graph.yaml'
        if default_path.exists():
            try:
                self.resource_graph.load_from_file(default_path)
            except Exception:
                # Silently continue if load fails
                pass
        
    def build(self, benchmark: bool = True, duration: int = 25):
        """
        Build resource graph by collecting information from all nodes in hostfile.

        :param benchmark: Whether to run performance benchmarks
        :param duration: Benchmark duration in seconds
        """
        # Get current hostfile
        jarvis = Jarvis.get_instance()
        if not jarvis.hostfile:
            raise ValueError("No hostfile set. Use 'jarvis hostfile set <path>' first.")
            
        hostfile = jarvis.hostfile
        nodes = hostfile.hosts
        
        if not nodes:
            raise ValueError("Hostfile contains no hosts")
            
        logger.pipeline(f"Building resource graph for {len(nodes)} nodes...")
        
        # Clear existing resource graph
        self.resource_graph = ResourceGraph()
        
        # Collect resources from all nodes in parallel
        self._collect_from_nodes(nodes, benchmark, duration)
        
        # Save resource graph
        self._save()
        
        # Display summary
        self.resource_graph.print_summary()
        self.resource_graph.print_common_storage()
        
    def _collect_from_nodes(self, nodes: List[str], benchmark: bool, duration: int):
        """
        Collect resource information from multiple nodes in parallel.
        
        :param nodes: List of node hostnames/IPs
        :param benchmark: Whether to run benchmarks
        :param duration: Benchmark duration
        """
        def collect_from_node(hostname: str) -> Dict[str, Any]:
            """Collect from a single node."""
            try:
                logger.package(f"Collecting resources from {hostname}...")
                
                # Get jarvis singleton  
                jarvis = Jarvis.get_instance()
                
                # Get current hostname using LocalExec to compare
                exec_info_hostname = LocalExecInfo(collect_output=True, hide_output=True)
                hostname_result = LocalExec('hostname', exec_info_hostname)
                current_hostname = hostname_result.stdout.get('localhost', '').strip()
                
                # Use local execution for localhost, otherwise use SSH
                if hostname in ['localhost', '127.0.0.1'] or hostname == current_hostname:
                    exec_info = LocalExecInfo(
                        collect_output=True,
                        hide_output=True
                    )
                else:
                    # Create a temporary hostfile for this specific node
                    from jarvis_cd.util.hostfile import Hostfile
                    single_host_hostfile = Hostfile([hostname])
                    
                    # Create execution info for this node
                    exec_info = PsshExecInfo(
                        hostfile=single_host_hostfile,
                        collect_output=True,
                        hide_output=True
                    )
                
                # Build command string
                cmd_parts = ['/mnt/home/Projects/iowarp/ppi-jarvis-cd/bin/jarvis_resource_graph']
                if not benchmark:
                    cmd_parts.append('--no-benchmark')
                if duration != 25:
                    cmd_parts.extend(['--duration', str(duration)])
                cmd = ' '.join(cmd_parts)
                
                logger.debug(f"Command to execute: {cmd}")
                
                # Execute resource collection based on execution type
                if exec_info.exec_type.name == 'LOCAL':
                    executor = LocalExec(cmd, exec_info)
                else:
                    from jarvis_cd.shell import Exec
                    executor = Exec(cmd, exec_info)
                
                # Get results
                exit_codes = executor.exit_code
                
                logger.debug(f"Exit codes: {exit_codes}")
                logger.debug(f"Stdout: {executor.stdout}")
                logger.debug(f"Stderr: {executor.stderr}")
                
                # Check for errors
                if exit_codes.get(hostname, 1) != 0:
                    error_msg = executor.stderr.get(hostname, "Unknown error")
                    logger.error(f"Failed to collect from {hostname}: {error_msg}")
                    return None
                    
                # Parse JSON output
                json_output = executor.stdout.get(hostname, "")
                if not json_output.strip():
                    logger.error(f"No output from {hostname}")
                    return None
                    
                resource_data = json.loads(json_output)
                logger.package(f"Collected {len(resource_data.get('fs', []))} storage devices from {hostname}")
                
                return resource_data
                
            except Exception as e:
                logger.error(f"Error collecting from {hostname}: {e}")
                return None
                
        # Use ThreadPoolExecutor for parallel collection
        max_workers = min(len(nodes), 10)  # Limit concurrent connections
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all collection tasks
            future_to_hostname = {
                executor.submit(collect_from_node, hostname): hostname 
                for hostname in nodes
            }
            
            # Process results as they complete
            for future in as_completed(future_to_hostname):
                hostname = future_to_hostname[future]
                try:
                    resource_data = future.result()
                    if resource_data:
                        # Add to resource graph
                        self.resource_graph.add_node_data(hostname, resource_data)
                        logger.success(f"Added resources from {hostname} to graph")
                    else:
                        logger.warning(f"No resource data collected from {hostname}")
                        
                except Exception as e:
                    logger.error(f"Exception processing {hostname}: {e}")
                    
    def _save(self):
        """Save resource graph to file."""
        # Save to user's home directory for private machine storage
        output_file = Path.home() / '.ppi-jarvis' / 'resource_graph.yaml'
        output_file.parent.mkdir(exist_ok=True)

        self.resource_graph.save_to_file(output_file)
        
    def load(self, file_path: Optional[Path] = None):
        """
        Load resource graph from file.

        :param file_path: Path to resource graph file (default: ~/.ppi-jarvis/resource_graph.yaml)
        """
        if file_path is None:
            file_path = Path.home() / '.ppi-jarvis' / 'resource_graph.yaml'
            
        if not file_path.exists():
            raise FileNotFoundError(f"Resource graph file not found: {file_path}")
            
        self.resource_graph.load_from_file(file_path)
        logger.success(f"Loaded resource graph from {file_path}")
        
    def show(self):
        """Display the current resource graph YAML file."""
        # Get default resource graph path
        default_path = Path.home() / '.ppi-jarvis' / 'resource_graph.yaml'

        if not default_path.exists():
            logger.warning("No resource graph found. Run 'jarvis rg build' first.")
            return

        # Read and print raw YAML file contents
        with open(default_path, 'r') as f:
            print(f.read())
        
    def show_node_details(self, hostname: str):
        """
        Show detailed storage information for a specific node.
        
        :param hostname: Hostname to show details for
        """
        if not self.resource_graph.get_all_nodes():
            # Try to load the current resource graph
            try:
                self.load()
            except FileNotFoundError:
                logger.warning("No resource graph loaded. Run 'jarvis rg build' first.")
                return
            
        self.resource_graph.print_node_details(hostname)
        
    def list_nodes(self):
        """List all nodes in the resource graph."""
        if not self.resource_graph.get_all_nodes():
            # Try to load the current resource graph
            try:
                self.load()
            except FileNotFoundError:
                logger.warning("No nodes in resource graph. Run 'jarvis rg build' first.")
                return
        
        nodes = self.resource_graph.get_all_nodes()
            
        logger.info(f"Nodes in resource graph ({len(nodes)}):")
        for node in sorted(nodes):
            storage_count = len(self.resource_graph.get_node_storage(node))
            logger.info(f"  {node}: {storage_count} storage devices")
            
    def filter_by_type(self, dev_type: str):
        """
        Show storage devices filtered by type.
        
        :param dev_type: Device type to filter by (ssd, hdd, etc.)
        """
        if not self.resource_graph.get_all_nodes():
            logger.warning("No resource graph loaded. Run 'jarvis rg build' first.")
            return
            
        filtered = self.resource_graph.filter_by_type(dev_type)
        
        if not filtered:
            logger.warning(f"No {dev_type} devices found")
            return
            
        logger.info(f"=== {dev_type.upper()} Storage Devices ===")
        for hostname, devices in filtered.items():
            logger.info(f"\n{hostname}:")
            for device in devices:
                perf_info = ""
                if device.randwrite_4k_bw != 'unknown' and device.seqwrite_1m_bw != 'unknown':
                    perf_info = f" [4K: {device.randwrite_4k_bw}, 1M: {device.seqwrite_1m_bw}]"
                logger.info(f"  {device.mount}: {device.avail}{perf_info}")
                
    def get_common_mounts(self) -> List[str]:
        """Get list of common mount points."""
        return list(self.resource_graph.get_common_storage().keys())
        
    def show_path(self):
        """Show the path to the current resource graph file."""
        # Default path where resource graph is stored
        default_path = Path.home() / '.ppi-jarvis' / 'resource_graph.yaml'
        
        if default_path.exists():
            # Print only the path for shell command substitution
            print(default_path)
        else:
            # Exit with error code for missing file
            print(f"Error: No resource graph found at {default_path}", file=sys.stderr)
            print("Run 'jarvis rg build' to create a resource graph", file=sys.stderr)
            sys.exit(1)