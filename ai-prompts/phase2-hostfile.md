## Hostfile
Implement the hostfile class. Put in jarvis_cd.util.

Hostfiles contain a set of machines.

Host Text Files
Hostfiles can be stored as text files on a filesystem. They have the following syntax:

ares-comp-01
ares-comp-[02-04]
ares-comp-[05-09,11,12-14]-40g

Hostfile Import
from jarvis_util.util.hostfile import Hostfile

Hostfile Constructor
The hostfile has the following constructor:

```python
class Hostfile:
    """
    Parse a hostfile or store a set of hosts passed in manually.
    """

    def __init__(self, path=None, hosts=None, hosts_ip=None,
                 text=None, find_ips=True, load_path=True):
        """
        Constructor. Parse hostfile or store existing host list.

        :param path: The path to the hostfile
        :param hosts: a list of strings representing all hostnames
        :param hosts_ip: a list of strings representing all host IPs
        :param text: Text of a hostfile
        :param find_ips: Whether to construct host_ip and all_host_ip fields
        :param load_path: whether or not path should exist and be read from on init
        """

    def subset(self, count, path=None):
        return Hostfile(path, hosts=self.hosts[0:count], find_ips=self.find_ips, load_path=False) 

    def copy(self):
        return self.subset(len(self))

    def is_local(self):
        """
        Whether this file contains only 'localhost'

        :return: True or false
        """
        if len(self) == 0:
            return True
        if len(self.hosts) == 1:
            if self.hosts[0] == 'localhost':
                return True
            if self.hosts[0] == socket.gethostbyname('localhost'):
                return True
        if len(self.hosts_ip) == 1:
            if self.hosts_ip[0] == socket.gethostbyname('localhost'):
                return True
        return False

    def save(self, path): 
        self.path = path
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write('\n'.join(self.hosts))
        return self

    def list(self):
        return [Hostfile(hosts=[host]) for host in self.hosts]

    def enumerate(self):
        return enumerate(self.list())

    def host_str(self, sep=','):
        return sep.join(self.hosts)

    def ip_str(self, sep=','):
        return sep.join(self.hosts_ip)
```

Hostfile for the current machine
To get the localhost file:

hostfile = Hostfile()

Hostfile from a filesystem
To load a hostfile from the filesystem:

hostfile = Hostfile(hostfile=f'{HERE}/test_hostfile.txt')

Host names and IPs
To get the host names and IP addresses, the Hostfile stores the hosts and hosts_ip variables. They are lists of strings.

hostfile = Hostfile()
print(hostfile.hosts)
print(hostfile.hosts_ip)

Output:

['localhost']
['127.0.0.1']