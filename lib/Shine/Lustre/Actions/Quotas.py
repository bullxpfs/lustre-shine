from ClusterShell.MsgTree import MsgTree
from ClusterShell.NodeSet import NodeSet

from Shine.Lustre import ServerError
from Shine.Lustre.Actions.Modules import ServerAction
from Shine.Lustre.Actions.Action import CommonAction, Action, \
                                        ACT_OK, ACT_ERROR

class HandleQuotas(ServerAction):
    """
    Handle quotas on MGS
    """

    NAME = 'handlequotas'

    def __init__(self, srv, fs, type='', quota_type='ug'):
        if fs is None:
            raise ServerError(srv, "A filesystem must be specified")

        ServerAction.__init__(self, srv)
        self._fs = fs
        self._fsname = self._fs.fs_name
        self._type = type
        self._quota_type = quota_type

        self._outputs = MsgTree()
        self._silentnodes = NodeSet() # Error nodes without output

        if self._fs.debug:
            print "HandleQuotas action for '%s' on %s" % \
                    (self._type,
                     self.server.hostname)

    def _shell(self):
        command = "lctl conf_param %s.quota.%s=%s" % \
                    (self._fsname, self._type, self._quota_type)

        self.task.shell(command, nodes=self.server.hostname, handler=self)

    def ev_read(self, worker):
        self._outputs.add(worker.current_node, worker.current_msg)

    def ev_hup(self, worker):
        """Keep a list of node, without output, with a return code != 0"""
        # If this node was on error
        if worker.current_rc != 0:
            # If there is no known outputs
            if self._outputs.get(worker.current_node) is None:
                self._silentnodes.add(worker.current_node)

    def ev_close(self, worker):
        """
        Check process termination status and set action status.
        """
        Action.ev_close(self, worker)

        self.server.lustre_check()

        # Action timed out
        if worker.did_timeout():
            self.set_status(ACT_ERROR)
            return

        status = ACT_OK

        # Gather nodes by return code
        for rc, nodes in worker.iter_retcodes():
            # Remote command returns only RUNTIME_ERROR (See RemoteCommand)
            # some common remote errors:
            # rc 127 = command not found
            # rc 126 = found but not executable
            # rc 1 = python failure...
            if rc != 0:

                # If there is at least one error, the action is on error.
                status = ACT_ERROR

                # Gather these nodes by buffer
                key = nodes.__contains__
                for buffers, nodes in self._outputs.walk(match=key):
                    # Handle proxy command error
                    nodes = NodeSet.fromlist(nodes)
                    msg = "Remote action %s failed: %s\n" % \
                                                        (self.NAME, buffers)
                    self._fs._handle_shine_proxy_error(nodes, msg)

        # Raise an error for nodes without output
        if len(self._silentnodes) > 0:
            msg = "Remote action %s failed: No response" % self.action
            self.fs._handle_shine_proxy_error(self._silentnodes, msg)

        self.set_status(status)
