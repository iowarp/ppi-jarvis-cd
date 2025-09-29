from jarvis_cd.core.pkg import Service, Color
from jarvis_cd.shell import Exec, SshExecInfo, PsshExecInfo
from jarvis_cd.shell.process import Kill
from jarvis_cd.util.hostfile import Hostfile
import os


class OrangefsFuse:
    def fuse_start(self):
        # start pfs servers 
        for host in self.server_hosts:
            server_start_cmds = [
                # f"pvfs2-server {self.config['pfs_conf']} -f -a {host}",
                f"pvfs2-server {self.config['pfs_conf']} -a {host}"
            ]
            Exec(server_start_cmds,
                 SshExecInfo(hostfile=Hostfile(all_hosts=[host]),
                             env=self.env))
        self.status()

        # start pfs client
        md_list = self.md_hosts.list()
        for i,client in self.client_hosts.enumerate():
            mdm_ip = md_list[i % len(self.md_hosts)].hosts_ip[0]
            start_client_cmds = [
                "pvfs2fuse -o fs_spec={protocol}://{ip}:{port}/{name} {mount_point}".format(
                    protocol=self.config['protocol'],
                    port=self.config['port'],
                    ip=mdm_ip,
                    name=self.config['name'],
                    mount_point=self.config['mount'])
            ]
            Exec(start_client_cmds,
                 SshExecInfo(hostfile=client,
                             env=self.env))

    def fuse_stop(self):
        cmds = [
            f"fusermount -u {self.config['mount']}"
        ]
        Exec(cmds, PsshExecInfo(hosts=self.client_hosts,
                                env=self.env))
        self.log(f"Unmounting {self.config['mount']} on each client", Color.YELLOW)

        Kill('.*pvfs2-client.*', PsshExecInfo(hosts=self.client_hosts,
                                        env=self.env))
        Kill('pvfs2-server',
             PsshExecInfo(hosts=self.server_hosts,
                          env=self.env))
        Exec("pgrep -la pvfs2-server", PsshExecInfo(hosts=self.client_hosts,
                                env=self.env))
