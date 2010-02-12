# FileSystem.py -- Lustre file system configuration
# Copyright (C) 2007, 2008 CEA
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
#
# $Id$


from Globals import Globals
from Model import Model
from Exceptions import *
from TuningModel import TuningModel

from ClusterShell.NodeSet import NodeSet

from NidMap import NidMap
from TargetDevice import TargetDevice

from Backend.Backend import Backend

import copy
import os
import sys


class FileSystem(Model):
    """
    Lustre File System Configuration class.
    """
    def __init__(self, fs_name=None, lmf=None, tuning_file=None):
        """ Initialize File System config
        """
        self.backend = None

        globals = Globals()

        fs_conf_dir = os.path.expandvars(globals.get_conf_dir())
        fs_conf_dir = os.path.normpath(fs_conf_dir)

        # Load the file system from model or extended model
        if not fs_name and lmf:
            Model.__init__(self, lmf)

            self.xmf_path = "%s/%s.xmf" % (fs_conf_dir, self.get_one('fs_name'))

            self._setup_target_devices()

            # Reload
            self.set_filename(self.xmf_path)

        elif fs_name:
            self.xmf_path = "%s/%s.xmf" % (fs_conf_dir, fs_name)
            Model.__init__(self, self.xmf_path)

        self.fs_name = self.get_one('fs_name')
        if len(self.fs_name) > 8:
            raise ConfigException("filesystem name `%s' is invalid (must be 1-8 chars)" % \
                    self.fs_name)

        # Set nodes to nids mapping using the NidMap helper class
        self.nid_map = NidMap.fromlist(self.get('nid_map'))
        
        # Initialize the tuning model to None if no special tuning configuration
        # is provided
        self.tuning_model = None
        
        if tuning_file:
            # It a tuning configuration file is provided load it
            self.tuning_model = TuningModel(tuning_file)
        else:
            self.tuning_model = TuningModel()

        #self._start_backend()

    def _start_backend(self):
        """
        Load and start backend subsystem once
        """
        if not self.backend:

            from Backend.BackendRegistry import BackendRegistry

            # Start the selected config backend system.
            self.backend = BackendRegistry().get_selected()
            if self.backend:
                self.backend.start()

        return self.backend

    def _setup_target_devices(self):
        """ Generate the eXtended Model File XMF
        """
        self._start_backend()

        for target in [ 'mgt', 'mdt', 'ost' ]:

            if self.backend:

                # Returns a list of TargetDevices
                candidates = copy.copy(self.backend.get_target_devices(target))

                try:
                    # Save the model target selection
                    target_models = copy.copy(self.get(target))
                except KeyError, e:
                    raise ConfigException("No %s target found" %(target))

                # Delete it (to be replaced... see below)
                self.delete(target)
                 
                # Iterates on ModelDevices
                i = 0
                for target_model in target_models:
                    result = target_model.match_device(candidates)
                    if target_model.get('mode')[0] == 'external':
                        self.add(target, str(target_model))
                        continue

                    if len(result) == 0:
                        raise ConfigDeviceNotFoundError(target_model)
                    for matching in result:
                        candidates.remove(matching)
                        #
                        # target index is now mandatory in XMF files
                        if not matching.has_index():
                            matching.add_index(i)
                            i += 1

                        # `matching' is a TargetDevice, we want to add it to the
                        # underlying Model object. The current way to do this to
                        # create a configuration line string (performed by
                        # TargetDevice.getline()) and then call Model.add(). 
                        # TODO: add methods to Model/ModelDevice to avoid the use
                        #       of temporary configuration string line.
                        self.add(target, matching.getline())
            else:
                # no backend support

                devices = copy.copy(self.get_with_dict(target))

                self.delete(target)

                target_devices = []
                i = 0
                for dict in devices:
                    t = TargetDevice(target, dict)
                    if not t.has_index():
                        t.add_index(i)
                        i += 1
                    target_devices.append(TargetDevice(target, dict))
                    self.add(target, t.getline())

                if len(target_devices) == 0:
                    raise ConfigDeviceNotFoundError(self)

        # Save XMF
        self.save(self.xmf_path, "Shine Lustre file system config file for %s" % \
                self.get_one('fs_name'))
            
    def get_nid(self, node):
        try:
            return self.nid_map[node]
        except KeyError:
            raise ConfigException("Cannot get NID for %s, aborting. Please verify `nid_map' configuration." % node)

    def __str__(self):
        return ">> BACKEND:\n%s\n>> MODEL:\n%s" % (self.backend, Model.__str__(self))

    def close(self):
        if self.backend:
            self.backend.stop()
            self.backend = None
    
    def register_client(self, node):
        """
        This function aims to register a new client that will be able to mount the
        file system.
        Parameters:
        @type node: string
        @param node : is the new client node name
        """
        if self._start_backend():
            self.backend.register_client(self.fs_name, node)
        
    def unregister_client(self, node):
        """
        This function aims to unregister a client of this  file system
        Parameters:
        @type node: string
        @param node : is name of the client node to unregister
        """
        if self._start_backend():
            self.backend.unregister_client(self.fs_name, node)
    
    def _set_status_client(self, node, status, options):
        """
        This function is used to change specified client status.
        """
        if self._start_backend():
            self.backend.set_status_client(self.fs_name, node, status, options)

    def set_status_client_mount_complete(self, node, options):
        """
        This function is used to set the specified client status
        to MOUNT_COMPLETE
        """
        self._set_status_client(node, Backend.MOUNT_COMPLETE, options)

    def set_status_client_mount_failed(self, node, options):
        """
        This function is used to set the specified client status
        to MOUNT_FAILED
        """
        self._set_status_client(node, Backend.MOUNT_FAILED, options)

    def set_status_client_mount_warning(self, node, options):
        """
        This function is used to set the specified client status
        to MOUNT_WARNING
        """
        self._set_status_client(node, Backend.MOUNT_WARNING, options)

    def set_status_client_umount_complete(self, node, options):
        """
        This function is used to set the specified client status
        to UMOUNT_COMPLETE
        """
        self._set_status_client(node, Backend.UMOUNT_COMPLETE, options)

    def set_status_client_umount_failed(self, node, options):
        """
        This function is used to set the specified client status
        to UMOUNT_FAILED
        """
        self._set_status_client(node, Backend.UMOUNT_FAILED, options)

    def set_status_client_umount_warning(self, node, options):
        """
        This function is used to set the specified client status
        to UMOUNT_WARNING
        """
        self._set_status_client(node, Backend.UMOUNT_WARNING, options)

    def get_status_clients(self):
        """
        This function returns the status of each clients
        involved in the current file system.
        """
        if self._start_backend():
            return self.backend.get_status_clients(self.fs_name)

    def _set_status_target(self, target, status, options):
        """
        This function is used to change the specified target status.
        """
        if self._start_backend():
            self.backend.set_status_target(self.fs_name, target, 
                status, options)

    def set_status_target_unknown(self, target, options):
        """
        This function is used to set the specified target status
        to UNKNOWN
        """
        self._set_status_target(target, Backend.TARGET_UNKNOWN, options)

    def set_status_target_ko(self, target, options):
        """
        This function is used to set the specified target status
        to KO
        """
        self._set_status_target(target, Backend.TARGET_KO, options)

    def set_status_target_available(self, target, options):
        """
        This function is used to set the specified target status
        to AVAILABLE
        """
        # Set the fs_name to Free since these targets are availble
        # which means not used by any file system.
        self._set_status_target(target, Backend.TARGET_AVAILABLE, options)

    def set_status_target_formating(self, target, options):
        """
        This function is used to set the specified target status
        to FORMATING
        """
        self._set_status_target(target, Backend.TARGET_FORMATING, options)

    def set_status_target_format_failed(self, target, options):
        """
        This function is used to set the specified target status
        to FORMAT_FAILED
        """
        self._set_status_target(target, Backend.TARGET_FORMAT_FAILED, options)

    def set_status_target_formated(self, target, options):
        """
        This function is used to set the specified target status
        to FORMATED
        """
        self._set_status_target(target, Backend.TARGET_FORMATED, options)

    def set_status_target_offline(self, target, options):
        """
        This function is used to set the specified target status
        to OFFLINE
        """
        self._set_status_target(target, Backend.TARGET_OFFLINE, options)

    def set_status_target_starting(self, target, options):
        """
        This function is used to set the specified target status
        to STARTING
        """
        self._set_status_target(target, Backend.TARGET_STARTING, options)

    def set_status_target_online(self, target, options):
        """
        This function is used to set the specified target status
        to ONLINE
        """
        self._set_status_target(target, Backend.TARGET_ONLINE, options)

    def set_status_target_critical(self, target, options):
        """
        This function is used to set the specified target status
        to CRITICAL
        """
        self._set_status_target(target, Backend.TARGET_CRITICAL, options)

    def set_status_target_stopping(self, target, options):
        """
        This function is used to set the specified target status
        to STOPPING
        """
        self._set_status_target(target, Backend.TARGET_STOPPING, options)

    def set_status_target_unreachable(self, target, options):
        """
        This function is used to set the specified target status
        to UNREACHABLE
        """
        self._set_status_target(target, Backend.TARGET_UNREACHABLE, options)

    def get_status_targets(self):
        """
        This function returns the status of each targets
        involved in the current file system.
        """
        if self._start_backend():
            return self.backend.get_status_targets(self.fs_name)

    def register(self):
        """
        This function aims to register the file system configuration
        to the backend.
        """
        if self._start_backend():
            return self.backend.register_fs(self)

    def unregister(self):
        """
        This function aims to remove a file system configuration from
        the backend.        
        """
        result = 0
        if self._start_backend():
            result = self.backend.unregister_fs(self)

        if not result:
            os.unlink(self.xmf_path)

        return result

    def _set_status(self, status, options):
        """
        This function is used to change the specified filesystem status.
        """
        if self._start_backend():
            self.backend.set_status_fs(self.fs_name, status, options)

    def set_status_installed(self, options):
        """
        This function is used to set the specified filesystem status
        to INSTALLED
        """
        self._set_status(Backend.FS_INSTALLED, options)

    def set_status_formating(self, options):
        """
        This function is used to set the specified filesystem status
        to FORMATING
        """
        self._set_status(Backend.FS_FORMATING, options)

    def set_status_formated(self, options):
        """
        This function is used to set the specified filesystem status
        to FORMATED
        """
        self._set_status(Backend.FS_FORMATED, options)

    def set_status_starting(self, options):
        """
        This function is used to set the specified filesystem status
        to STARTING
        """
        self._set_status(Backend.FS_STARTING, options)

    def set_status_online(self, options):
        """
        This function is used to set the specified filesystem status
        to ONLINE
        """
        self._set_status(Backend.FS_ONLINE, options)

    def set_status_mounted(self, options):
        """
        This function is used to set the specified filesystem status
        to MOUNTED
        """
        self._set_status(Backend.FS_MOUNTED, options)

    def set_status_stopping(self, options):
        """
        This function is used to set the specified filesystem status
        to STOPPING
        """
        self._set_status(Backend.FS_STOPPING, options)

    def set_status_offline(self, options):
        """
        This function is used to set the specified filesystem status
        to OFFLINE
        """
        self._set_status(Backend.FS_OFFLINE, options)

    def set_status_checking(self, options):
        """
        This function is used to set the specified filesystem status
        to CHECKING
        """
        self._set_status(Backend.FS_CHECKING, options)

    def set_status_unknown(self, options):
        """
        This function is used to set the specified filesystem status
        to UNKNOWN
        """
        self._set_status(Backend.FS_UNKNOWN, options)

    def set_status_warning(self, options):
        """
        This function is used to set the specified filesystem status
        to WARNING
        """
        self._set_status(Backend.FS_WARNING, options)

    def set_status_critical(self, options):
        """
        This function is used to set the specified filesystem status
        to CRITICAL
        """
        self._set_status(Backend.FS_CRITICAL, options)

    def set_status_online_failed(self, options):
        """
        This function is used to set the specified filesystem status
        to ONLINE_FAILED
        """
        self._set_status(Backend.FS_ONLINE_FAILED, options)

    def set_status_offline_failed(self, options):
        """
        This function is used to set the specified filesystem status
        to OFFLINE_FAILED
        """
        self._set_status(Backend.FS_OFFLINE_FAILED, options)

    def get_status(self):
        """
        This function returns the status of the current file system.
        """
        return self.backend.get_status_fs(self.fs_name)

