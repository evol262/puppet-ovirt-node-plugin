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
        # The py snippet below will only change the runtime configuratio (NFSv4 domain)
        # To make persistent changes we'll need to use the ovirt.node.config.defaults
        # module, which gives us access to all topics which are covered by Node's logic.
        # ovirt.node.utils.* modules only change the runtime config, but don't persist the
        # changes.
        # See ssh_pwauth for a complete example
        python("-c 'from ovirt.node.utils.storage import NFSv4; NFSv4.domain(#{domain}'")
    end

    def iscsi_initiator=(name) do
        python("-c 'from ovirt.node.utils.storage import iSCSI; iSCSI.initiator_name(#{name})'")
    end

    def ssh_pwauth=(bool) do
        # It needs to be ensured that #{bool} is either True or False (so a bool in py syntax)
        python("-c 'from ovirt.node.config import defaults; model = defaults.SSH() ; model.update(#{bool}) ; tx = model.transaction() ; tx()'")
    end

end
