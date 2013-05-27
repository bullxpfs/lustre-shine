# Status.py -- Status of file system
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

from Shine.Configuration.Configuration import Configuration
from Shine.Configuration.Globals import Globals 
from Shine.Configuration.Exceptions import *
from Base.FSCommand import FSCommand

# ----------------------------------------------------------------------
# * shine status
# ----------------------------------------------------------------------
class Status(FSCommand):

    def get_name(self):
        return "status"

    def get_params_desc(self):
        return "-f <fsname> -t <target>"

    def get_desc(self):
        return "Status of file system servers."

    def fs_execute(self, fs, fs_target):
        fs.status(fs_target)

