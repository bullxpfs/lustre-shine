# Fsck.py -- Check backend file system for each target
# Copyright (C) 2010 BULL S.A.S
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

import sys

from Shine.Commands.Status import Status

# Command base class
from Shine.Commands.Base.FSLiveCommand import FSTargetLiveCriticalCommand
from Shine.Commands.Base.CommandRCDefs import RC_OK, RC_ST_EXTERNAL, \
                                              RC_FAILURE, RC_TARGET_ERROR, \
                                              RC_CLIENT_ERROR, RC_RUNTIME_ERROR
# Lustre events
import Shine.Lustre.EventHandler
from Shine.Commands.Base.FSEventHandler import FSGlobalEventHandler

from Shine.Lustre.FileSystem import MOUNTED, RECOVERING, EXTERNAL, OFFLINE, \
                                    TARGET_ERROR, CLIENT_ERROR, RUNTIME_ERROR

class GlobalFsckEventHandler(FSGlobalEventHandler):

    def handle_pre(self, fs):
        # attach fs to this handler
        if self.verbose > 0:
            count = len(list(fs.managed_components()))
            servers = fs.managed_component_servers()
            print "Starting fsck of %d targets on %s" % (count, servers)

    def handle_post(self, fs):
        if self.verbose > 0:
            Status.status_view_fs(fs, show_clients=False)

    def ev_fscktarget_start(self, node, comp):
        self.update_config_status(comp, "checking")

        if self.verbose > 1:
            print "%s: Starting fsck of %s %s (%s)" % (node, comp.TYPE.upper(), \
                    comp.get_id(), comp.dev)

        self.update()

    def ev_fscktarget_done(self, node, comp):
        self.update_config_status(comp, "succeeded")

        if self.verbose > 1:
            print "%s: Fsck of %s %s (%s) succeeded" % \
                    (node, comp.TYPE.upper(), comp.get_id(), comp.dev)

        self.update()

    def ev_fscktarget_failed(self, node, comp, rc, message):
        self.update_config_status(comp, "failed")

        print "%s: Fsck of %s %s (%s) failed with error %d" % \
                (node, comp.TYPE.upper(), comp.get_id(), comp.dev, rc)
        print message

        self.update()

    def update_config_status(self, target, status):
        # Retrieve the right target from the configuration
        target_list = [self.fs_conf.get_target_from_tag_and_type(target.tag,
            target.TYPE.upper())]

        # Change the status of targets to avoid their use
        # in an other file system
        if status == "succeeded":
            self.fs_conf.set_status_targets_offline(target_list, None)
            self.fs_conf.set_status_targets_formated(target_list, None)
        elif status == "failed":
            self.fs_conf.set_status_targets_ko(target_list, None)
        else:
            self.fs_conf.set_status_targets_checking(target_list, None)


class LocalFsckEventHandler(Shine.Lustre.EventHandler.EventHandler):

    def __init__(self, verbose=1):
        Shine.Lustre.EventHandler.EventHandler.__init__(self)
        self.verbose = verbose

    def ev_fscktarget_start(self, node, comp):
        print "Starting fsck of %s %s (%s)" % (comp.TYPE.upper(), \
                comp.get_id(), comp.dev)
        sys.stdout.flush()

    def ev_fscktarget_done(self, node, comp):
        print "Fsck of %s %s (%s) succeeded" % \
                (comp.TYPE.upper(), comp.get_id(), comp.dev)

    def ev_fscktarget_failed(self, node, comp, rc, message):
        print "Fsck of %s %s (%s) failed with error %d" % \
                (comp.TYPE.upper(), comp.get_id(), comp.dev, rc)
        print message


class Fsck(FSTargetLiveCriticalCommand):
    """
    shine fsck -f <fsname> [-t <target>] [-i <index(es)>] [-n <nodes>]
    """
    
    NAME = "fsck"
    DESCRIPTION = "Fsck on targets backend file system."

    GLOBAL_EH = GlobalFsckEventHandler
    LOCAL_EH = LocalFsckEventHandler

    TARGET_STATUS_RC_MAP = { \
            MOUNTED : RC_FAILURE,
            EXTERNAL : RC_ST_EXTERNAL,
            RECOVERING : RC_FAILURE,
            OFFLINE : RC_OK,
            TARGET_ERROR : RC_TARGET_ERROR,
            CLIENT_ERROR : RC_CLIENT_ERROR,
            RUNTIME_ERROR : RC_RUNTIME_ERROR }

    def execute_fs(self, fs, fs_conf, eh, vlevel):

        # Warn if trying to act on wrong nodes
        if not self.nodes_support.check_valid_list(fs.fs_name, \
                fs.managed_component_servers(supports="fsck"), "fsck"):
            return RC_FAILURE

        if not self.ask_confirm("Fsck %s on %s: are you sure?" % (fs.fs_name,
                fs.managed_component_servers(supports='fsck'))):
            return RC_FAILURE

        # Call a pre_fsck method if defined by the event handler.
        if hasattr(eh, 'pre'):
            eh.pre(fs)
        
        # Notify backend of file system status mofication
        fs_conf.set_status_fs_checking()

        # Fsck really.
        status = fs.fsck(addopts = self.addopts.get_options(),
                         failover=self.target_support.get_failover())

        rc = self.fs_status_to_rc(status)

        if rc == RC_OK:
            # Notify backend of file system status mofication
            fs_conf.set_status_fs_offline()

            if vlevel > 0:
                print "Fsck successful."
        else:
            # Notify backend of file system status mofication
            fs_conf.set_status_fs_critical()

            if rc == RC_RUNTIME_ERROR:
                for nodes, msg in fs.proxy_errors:
                    print "%s: %s" % (nodes, msg)
            if vlevel > 0:
                print "Fsck failed"

        # Call a post_fsck method if defined by the event handler.
        if hasattr(eh, 'post'):
            eh.post(fs)

        return rc
