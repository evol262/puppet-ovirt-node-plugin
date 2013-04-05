require 'fileutils'

Puppet::Type.type(:ovirt_node).provide(:ovirt) do
    def exists?
        `openssl x509 -in /etc/pki/vdsm/certs/engine_web_ca.pem -noout -issuer`
        .match(/CN=CA-#{@resource[:address]}/ ? true : false
    end
