import socket
import re
import os
from typing import List, Optional, Union


class Hostfile:
    """
    Parse a hostfile or store a set of hosts passed in manually.
    """

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
        self.path = path
        self.find_ips = find_ips
        self.hosts = []
        self.hosts_ip = []
        
        # Initialize from different sources
        if hosts is not None:
            self.hosts = list(hosts)
        elif path is not None and load_path:
            self._load_from_path(path)
        elif text is not None:
            self._load_from_text(text)
        else:
            # Default to localhost
            self.hosts = ['localhost']
            
        # Set hosts_ip if provided, otherwise resolve if find_ips is True
        if hosts_ip is not None:
            self.hosts_ip = list(hosts_ip)
        elif find_ips:
            self._resolve_ips()
            
    def _load_from_path(self, path: str):
        """Load hostfile from filesystem path"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Hostfile not found: {path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        self._load_from_text(content)
        
    def _load_from_text(self, text: str):
        """Load hostfile from text content"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.hosts = []
        
        for line in lines:
            expanded_hosts = self._expand_host_pattern(line)
            self.hosts.extend(expanded_hosts)
            
    def _expand_host_pattern(self, pattern: str) -> List[str]:
        """
        Expand host patterns like:
        - ares-comp-01 -> ['ares-comp-01']
        - ares-comp-[02-04] -> ['ares-comp-02', 'ares-comp-03', 'ares-comp-04']
        - ares-comp-[05-09,11,12-14]-40g -> ['ares-comp-05-40g', ..., 'ares-comp-14-40g']
        """
        if '[' not in pattern:
            return [pattern]
            
        # Find bracket expressions
        bracket_match = re.search(r'\[([^\]]+)\]', pattern)
        if not bracket_match:
            return [pattern]
            
        bracket_content = bracket_match.group(1)
        prefix = pattern[:bracket_match.start()]
        suffix = pattern[bracket_match.end():]
        
        # Parse bracket content (ranges and individual numbers/letters)
        numbers = set()
        for part in bracket_content.split(','):
            part = part.strip()
            if '-' in part and not part.startswith('-'):
                # Range like "02-04", "12-14", or "a-c"
                range_parts = part.split('-')
                if len(range_parts) == 2:
                    start, end = range_parts
                    try:
                        # Try numeric range first
                        start_num = int(start)
                        end_num = int(end)
                        # Preserve zero-padding
                        width = max(len(start), len(end))
                        for i in range(start_num, end_num + 1):
                            numbers.add(str(i).zfill(width))
                    except ValueError:
                        # Try alphabetic range
                        if len(start) == 1 and len(end) == 1 and start.isalpha() and end.isalpha():
                            start_ord = ord(start.lower())
                            end_ord = ord(end.lower())
                            for i in range(start_ord, end_ord + 1):
                                char = chr(i)
                                # Preserve case from start character
                                if start.isupper():
                                    char = char.upper()
                                numbers.add(char)
                        else:
                            # If not numeric or single char range, treat as literal
                            numbers.add(part)
            else:
                # Individual item like "11" or "a"
                numbers.add(part)
                
        # Generate all combinations
        result = []
        for num in sorted(numbers):
            host = f"{prefix}{num}{suffix}"
            # Recursively expand if there are more brackets
            result.extend(self._expand_host_pattern(host))
            
        return result
        
    def _resolve_ips(self):
        """Resolve hostnames to IP addresses"""
        self.hosts_ip = []
        for host in self.hosts:
            try:
                if host == 'localhost':
                    ip = socket.gethostbyname('localhost')
                else:
                    ip = socket.gethostbyname(host)
                self.hosts_ip.append(ip)
            except socket.gaierror:
                # If resolution fails, use the hostname as IP
                self.hosts_ip.append(host)
                
    def subset(self, count: int, path: Optional[str] = None) -> 'Hostfile':
        """Return a subset of the first 'count' hosts"""
        return Hostfile(path=path, hosts=self.hosts[0:count], 
                       hosts_ip=self.hosts_ip[0:count] if self.hosts_ip else None,
                       find_ips=self.find_ips, load_path=False)
                       
    def copy(self) -> 'Hostfile':
        """Return a copy of this hostfile"""
        return self.subset(len(self))
        
    def is_local(self) -> bool:
        """
        Whether this file contains only 'localhost'

        :return: True or false
        """
        if len(self) == 0:
            return True
            
        if len(self.hosts) == 1:
            if self.hosts[0] == 'localhost':
                return True
            try:
                if self.hosts[0] == socket.gethostbyname('localhost'):
                    return True
            except socket.gaierror:
                pass
                
        if len(self.hosts_ip) == 1:
            try:
                if self.hosts_ip[0] == socket.gethostbyname('localhost'):
                    return True
            except socket.gaierror:
                pass
                
        return False
        
    def save(self, path: str) -> 'Hostfile':
        """Save hostfile to filesystem"""
        self.path = path
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write('\n'.join(self.hosts))
        return self
        
    def list(self) -> List['Hostfile']:
        """Return a list of single-host Hostfile objects"""
        return [Hostfile(hosts=[host], find_ips=self.find_ips, load_path=False) 
                for host in self.hosts]
                
    def enumerate(self):
        """Return enumerated list of single-host Hostfile objects"""
        return enumerate(self.list())
        
    def host_str(self, sep: str = ',') -> str:
        """Return hosts as a separated string"""
        return sep.join(self.hosts)
        
    def ip_str(self, sep: str = ',') -> str:
        """Return host IPs as a separated string"""
        return sep.join(self.hosts_ip)
        
    def is_subset(self) -> bool:
        """
        Return True if hostfile was created from a host list rather than a file.
        Used to determine whether to use --host or --hostfile in MPI commands.
        """
        return self.path is None
        
    def __len__(self) -> int:
        """Return number of hosts"""
        return len(self.hosts)
        
    def __iter__(self):
        """Iterate over hostnames"""
        return iter(self.hosts)
        
    def __getitem__(self, index):
        """Get host by index"""
        return self.hosts[index]
        
    def __str__(self) -> str:
        """String representation"""
        return f"Hostfile({len(self.hosts)} hosts: {self.host_str()})"
        
    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"Hostfile(hosts={self.hosts}, hosts_ip={self.hosts_ip})"