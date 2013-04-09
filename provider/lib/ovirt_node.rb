require 'fileutils'
require 'filetest'
require 'augeas'

Puppet::Type.type(:ovirt_node).provide(:ovirt) do
    commands :python => "/usr/bin/python"
    def instances
        config_vars = %w[hostname ssh_pwauth dns ip_address ip_gateway ip_netmask 
                         management_server use_strong_rng]
        if FileTests.exists?("/etc/pki/vdsm/certs/engine_web_ca.pem")
          engine = %x(openssl x509 -in /etc/pki/vdsm/certs/engine_web_ca.pem -noout -issuer).
              match(/CN=CA-(.*?)\.\d+$/)
          if engine?
              vars = {}
              augtool = %x(augtool print /files/etc/default/ovirt | grep = | awk '{print $1}')
              keys = Hash[keys.split("\n").collect.map { |x| [x, nil] } ]
              keys.each.key do |key|
                  if config_vars.include? "OVIRT_#{key}".downcase
                      Augeas::open do |aug|
                          x = aug.get(key)
                          vars[key.split("/").last.to_sym] = x
                      end
                  end
              end
              new(vars)
          end
        end
    end

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

    def ssh_pwauth=(bool) do
        python("-c 'from ovirt.node.config import defaults; defaults.SSH().update(#{bool})'")
    end


end
