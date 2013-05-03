Puppet::Type.newtype(:ovirt_node) do
    ensurable

    newparam(:address, :namevar => true) do
        desc "The address of the server"
    end

    newparam(:nfsdomain) do
        desc "The NFSv4 domain for the node"
    end

    newparam(:iscsi_initiator) do
        desc "The iSCSI Initiator Name"
    end

    newparam(:kdump) do
        desc "kdump configuration"
    end
    
    newparam(:ssh) do
        desc "Enable SSH authentication"
        newvalues(:True, :true, :False, :false)
        defaultto :False

        munge do |value|
            case value
            when :true
                :True
            when :false
                :False
            else
                super
            end
        end
    end

    newparam(:rsyslog) do 
        desc "RSyslog server"
    end

    newparam(:netconsole) do
        desc "Netconsole server"
    end

    newparam(:monitoring) do
        desc "Monitoring server"
    end
end
