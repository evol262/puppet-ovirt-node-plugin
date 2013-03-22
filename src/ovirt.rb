Facter.add(:operatingsystem) do
    has_weight 100_000_000
    confine :kernel => :linux
    setcode do
        if FileTest.exists?("/etc/default/version")
            txt = File.read("/etc/default/version")
            if txt =~ /^PRODUCT='(.*?)\s/
                $1
            end
        end
    end
end

Facter.add(:operatingsystemrelease) do
    confine :operatingsystem => %w{oVirt}
    setcode do
        if FileTest.exists?("/etc/default/version")
            txt = File.read("/etc/default/version")
            if txt =~ /^VERSION=(.*)/
                $1
            else
                "unknown"
            end
        end
    end
end
