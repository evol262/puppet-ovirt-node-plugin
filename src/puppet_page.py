#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# puppet_page.py - Copyright (C) 2013 Red Hat, Inc.
# Written by Ryan Barry <rbarry@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
from ovirt.node import plugins, valid, ui, utils
from ovirt.node.config.defaults import NodeConfigFileSection
from ovirt.node.plugins import Changeset
import logging
import socket
import re

"""
Configure Puppet
"""


LOGGER = logging.getLogger(__name__)


class Plugin(plugins.NodePlugin):
    _server = None

    def name(self):
        return "Puppet"

    def rank(self):
        return 105

    def model(self):
        cfg = Puppet().retrieve()
        model = {
            "puppet.enabled": True if cfg["enabled"] else False,
            "puppet.server": cfg["server"] or "puppet",
            "puppet.certname": cfg["certname"] or socket.gethostname()
        }
        return model

    def validators(self):
        return {"puppet.server": valid.FQDNOrIPAddress() | valid.Empty(),
                }

    def ui_content(self):
        ws = [ui.Header("header[0]", "Puppet Configuration"),
              ui.Checkbox("puppet.enabled", "Enable Puppet"),
              ui.Entry("puppet.server", "Puppet Server:"),
              ui.Entry("puppet.certname", "Puppet Certificate Name"),
              ui.Divider("divider[0]"),
              ]

        page = ui.Page("page", ws)
        page.buttons = [ui.SaveButton("action.register", "Save & Run")]

        self.widgets.add(page)
        return page

    def on_change(self, changes):
        pass

    def on_merge(self, effective_changes):
        self.logger.info("Saving Puppet config")
        changes = Changeset(self.pending_changes(False))
        effective_model = Changeset(self.model())
        effective_model.update(effective_changes)

        puppet_keys = ["puppet.enabled", "puppet.server", "puppet.certname"]
        if changes.contains_any(puppet_keys):
            Puppet().update(*effective_model.values_for(puppet_keys))

        self.logger.debug("Changes: %s" % changes)
        self.logger.debug("Effective Model: %s" % effective_model)

        txs = utils.Transaction("Configuring Puppet")

        if effective_changes.contains_any(["action.register"]):
            self.logger.debug("Connecting to puppet")
            txs += [ActivatePuppet()]

        if len(txs) > 0:
            progress_dialog = ui.TransactionProgressDialog("dialog.txs", txs,
                                                           self)
            progress_dialog.run()

        # Acts like a page reload
        return self.ui_content()


#
#
# Functions and classes to support the UI
#
#
class Puppet(NodeConfigFileSection):
    """Class to handle Puppet configuration in /etc/default/ovirt file

    >>> from ovirt.node.config.defaults import ConfigFile, SimpleProvider
    >>> fn = "/tmp/cfg_dummy"
    >>> cfgfile = ConfigFile(fn, SimpleProvider)
    >>> n = Puppet(cfgfile)
    >>> n.update("puppet.example.com")
    >>> sorted(n.retrieve().items())
    [(server, 'puppet.example.com')]
    """
    keys = ("OVIRT_PUPPET_ENABLED",
            "OVIRT_PUPPET_SERVER",
            "OVIRT_PUPPET_CERTIFICATE_NAME"
            )

    @NodeConfigFileSection.map_and_update_defaults_decorator
    def update(self, enabled, server, certname):
        valid.Boolean()(enabled)
        (valid.Empty() | valid.FQDNOrIPAddress())(server)
        (valid.Empty() | valid.FQDN())(certname)
        return {"OVIRT_PUPPET_ENABLED": "yes" if enabled else False}


class ActivatePuppet(utils.Transaction.Element):

    title = "Activating Puppet"

    def commit(self):

        self.logger.info("Connecting to Puppet server")

        cfg = Puppet().retrieve()

        with open("/etc/puppet/puppet.conf") as conf:
            lines = conf.readlines()
        with open("/etc/puppet/puppet.conf", "w") as conf:
            for line in lines:
                try:
                    item = re.match(r'^\s+(\w+) =', line).group(1)
                    if item in cfg:
                        print "matched"
                        conf.write(re.sub(r'(^.*?' + item + ' =).*', r'\1 "' +
                        cfg[item] + '"', line))
                except:
                    conf.write(line)

        utils.process.call("service puppet stop")
        #utils.process.check_call("puppet agent --test")
        #utils.process.call("service puppet start")
