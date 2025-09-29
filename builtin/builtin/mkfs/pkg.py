"""
This module provides classes and methods to create XFS or EXT4 filesystems.
"""
from jarvis_cd.core.pkg import Application
from jarvis_cd.shell import Exec, LocalExecInfo
from jarvis_cd.shell.process import Mkdir, MkfsXfs, MkfsExt4, Mount, Chown, Umount, Rmdir
import os


class Mkfs(Application):
    """
    This class provides methods to create XFS or EXT4 filesystems.
    """
    def _init(self):
        """
        Initialize paths
        """
        pass

    def _configure_menu(self):
        """
        Create a CLI menu for the configurator method.
        """
        return [
            {
                'name': 'device',
                'msg': 'The device to format (e.g., /dev/sda1)',
                'type': str,
                'default': None,
                'required': True
            },
            {
                'name': 'fs_type',
                'msg': 'The filesystem type to create (xfs or ext4)',
                'type': str,
                'default': 'xfs',
                'choices': ['xfs', 'ext4']
            },
            {
                'name': 'force',
                'msg': 'Force creation even if filesystem exists',
                'type': bool,
                'default': False
            },
            {
                'name': 'block_size',
                'msg': 'Block size in bytes',
                'type': int,
                'default': 4096
            },
            {
                'name': 'inode_size',
                'msg': 'Inode size in bytes (ext4 only)',
                'type': int,
                'default': 256
            },
            {
                'name': 'mount_point',
                'msg': 'Where to mount the filesystem after creation',
                'type': str,
                'default': None
            }
        ]

    def _configure(self, **kwargs):
        """
        Validates configuration parameters
        """
        if not self.config['device']:
            raise ValueError("Device parameter is required")
        
        if self.config['fs_type'] not in ['xfs', 'ext4']:
            raise ValueError("Filesystem type must be either 'xfs' or 'ext4'")

    def start(self):
        """
        Create the filesystem
        """
        # Create filesystem based on type
        if self.config['fs_type'] == 'xfs':
            self.log(f"Creating XFS filesystem on {self.config['device']}")
            MkfsXfs(self.config['device'],
                   LocalExecInfo(env=self.env,
                                sudo=True),
                   block_size=self.config['block_size'],
                   force=self.config['force']).run()
        else:  # ext4
            self.log(f"Creating EXT4 filesystem on {self.config['device']}")
            MkfsExt4(self.config['device'],
                    LocalExecInfo(env=self.env,
                                 sudo=True),
                    block_size=self.config['block_size'],
                    inode_size=self.config['inode_size'],
                    force=self.config['force']).run()

        # Mount the filesystem if mount point is specified
        if self.config['mount_point']:
            # Create mount point if it doesn't exist
            Mkdir(self.config['mount_point'],
                  LocalExecInfo(env=self.env,
                               sudo=True)).run()

            # Mount the filesystem
            Mount(self.config['device'],
                  self.config['mount_point'],
                  LocalExecInfo(env=self.env,
                               sudo=True),
                  options=['data=ordered']).run()
            self.log(f"Mounted filesystem at {self.config['mount_point']}")

            # Change ownership to current user
            uid = os.getuid()
            gid = os.getgid()
            self.log(f"Changing ownership of {self.config['mount_point']} to current user (uid={uid}, gid={gid})")
            Chown(self.config['mount_point'],
                  uid,
                  gid,
                  LocalExecInfo(env=self.env,
                               sudo=True)).run()

    def stop(self):
        """
        Unmount the filesystem if it was mounted
        """
        if self.config['mount_point']:
            self.log(f"Unmounting filesystem from {self.config['mount_point']}")
            Umount(self.config['mount_point'],
                   LocalExecInfo(env=self.env,
                                sudo=True)).run()

    def clean(self):
        """
        Clean up by unmounting and removing mount point if it exists
        """
        if self.config['mount_point']:
            # First unmount
            self.stop()
            
            # Then remove mount point directory
            self.log(f"Removing mount point directory {self.config['mount_point']}")
            Rmdir(self.config['mount_point'],
                  LocalExecInfo(env=self.env,
                               sudo=True)).run()

