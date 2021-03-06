# Backend.py -- File system config backend point of view
# Copyright (C) 2007-2013 CEA
#
# This file is part of shine
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.


NIEXC="Derived classes must implement."

class Backend:
    """
    An interface representing config backend storage resources for a file system.
    """

    MOUNT_COMPLETE = 1
    MOUNT_FAILED = 2
    MOUNT_WARNING = 3
    UMOUNT_COMPLETE = 4
    UMOUNT_FAILED = 5
    UMOUNT_WARNING = 6

    # Integers which represents the different target status
    TARGET_UNKNOWN=1
    TARGET_KO=2
    TARGET_AVAILABLE=3
    TARGET_FORMATING=4
    TARGET_FORMAT_FAILED=5
    TARGET_FORMATED=6
    TARGET_OFFLINE=7
    TARGET_STARTING=8
    TARGET_ONLINE=9
    TARGET_CRITICAL=10
    TARGET_STOPPING=11
    TARGET_UNREACHABLE=12
    TARGET_CHECKING=13

    def __init__(self):
        "Initializer."
        pass

    # Public accessors.

    def get_name(self):
        raise NotImplementedError(NIEXC)

    def get_desc(self):
        raise NotImplementedError(NIEXC)

    # Public methods.

    def start(self):
        """
        The config backend storage system has been selected.
        """
        raise NotImplementedError(NIEXC)

    def stop(self):
        """
        Stop operations
        """
        raise NotImplementedError(NIEXC)

    def get_target_devices(self, target, fs_name=None, update_mode=False):
        """
        Get the targets configuration, as a TargetDevice list (for mgt, mdt, ost).
        """
        raise NotImplementedError(NIEXC)

    def register_fs(self, fs):
        """
        This function is used to register a a filesystem configuration to the backend
        """
        raise NotImplementedError(NIEXC)

    def unregister_fs(self, fs):
        """
        This function is used to remove a filesystem configuration to the backend
        """
        raise NotImplementedError(NIEXC)

    def register_target(self, fs, target):
        """
        Set the specified `target', used by `fs', as 'in use' in the backend.

        This target could not be use anymore for other filesystems.
        """
        raise NotImplementedError(NIEXC)

    def unregister_target(self, fs, target):
        """
        Set the specified `target', used by `fs', as available in the backend.

        This target could be now reuse, for other targets of the same
        filesystem or any other one.
        """
        raise NotImplementedError(NIEXC)
