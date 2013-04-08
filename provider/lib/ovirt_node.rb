require 'fileutils'

Puppet::Type.type(:ovirt_node).provide(:ovirt) do
    commands :python => "/usr/bin/python"
    def exists?
        `openssl x509 -in /etc/pki/vdsm/certs/engine_web_ca.pem -noout -issuer`
        .match(/CN=CA-#{@resource[:address]}/ ? true : false
    end

    def nfsdomain=(domain) do
        python("-c 'from ovirt.node.utils.storage import NFSv4; NFSv4.domain(#{domain}'")
    end

    def iscsi_initiator=(name) do
        python("-c 'from ovirt.node.utils.storage import iSCSI; iSCSI.initiator_name(#{name})'")
    end
end
