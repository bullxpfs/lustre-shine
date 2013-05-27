# Start.py -- Lustre proxy action class : start
# Copyright (C) 2007 CEA
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

from Shine.Configuration.Globals import Globals
from Shine.Configuration.Configuration import Configuration

from Shine.Lustre.Actions.Action import ActionFailedError
from ProxyAction import ProxyAction

from Shine.Utilities.Cluster.NodeSet import NodeSet
from Shine.Utilities.Cluster.Event import EventHandler
from Shine.Utilities.Cluster.Task import Task
from Shine.Utilities.Cluster.Worker import Worker
from Shine.Utilities.AsciiTable import AsciiTable

class Start(ProxyAction):
    """
    File system start proxy action class.
    """

    def __init__(self, task, fs, target_name):
        ProxyAction.__init__(self, task)
        self.fs = fs
        self.target_name = target_name
        assert self.target_name != None

    def launch(self):
        """
        Proxy file system start command to target.
        """

        # Prepare proxy command
        command = "%s start -f %s -L -t %s" % (self.progpath, self.fs.fs_name, self.target_name)

        selected_nodes = self.fs.get_target_nodes(self.target_name)

        # Run cluster command
        self.task.shell(command, nodes=selected_nodes, handler=self)
        self.task.run()

    def ev_read(self, worker):
        print "%s: %s" % worker.get_last_read()

    def ev_close(self, worker):
        gdict = worker.gather_rc()
        for nodelist, rc in gdict.iteritems():
            if rc != 0:
                raise ActionFailedError(rc, "Start of %s failed on %s" % (self.target_name.upper(), nodelist.as_ranges()))

    
