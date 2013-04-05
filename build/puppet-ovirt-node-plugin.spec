Summary:        A plugin to make oVirt Node installs compatible with Puppet
Name:           puppet-ovirt-node-plugin
Version:        0.0.1
Release:        0%{?BUILD_NUMBER}%{?extra_release}%{?dist}
Source0:        %{name}-%{version}.tar.gz
License:        GPLv2+
Group:          Applications/System

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL:            http://www.ovirt.org/
BuildRequires:  automake autoconf
Requires:       ovirt-node >= 2.6.0
Requires:       puppet

BuildArch:      noarch

%define app_root %{_datadir}/%{name}
%define recipe_root %{_datadir}/ovirt-node-recipe

%description
Provides UI and associated scripts for integrating oVirt Node and Puppet

%package recipe
Summary:        Kickstarts for building oVirt Node isos including %{name}
Group:          Applications/System
Requires:       ovirt-node-recipe >= 2.6.0

%description recipe
Provides kickstart files for generating an oVirt Node ISO image containing
%{name}.

%prep
%setup -q


%build
aclocal && autoheader && automake --add-missing && autoconf


%configure
make


%install
%{__rm} -rf %{buildroot}
make install DESTDIR=%{buildroot}


%clean
%{__rm} -rf %{buildroot}


%post -p /bin/bash
cd /usr/share/ruby/vendor_ruby/facter
patch -p0 << EOF
--- operatingsystem.rb  2013-03-19 16:12:46.610079038 -0700
+++ operatingsystemnew.rb   2013-03-21 11:51:59.199657472 -0700
@@ -10,6 +10,9 @@
 #
 # Caveats:
 #
+#
+\$LOAD_PATH.unshift('/var/lib/puppet/facts')
+require 'ovirt.rb'
 
 Facter.add(:operatingsystem) do
   confine :kernel => :sunos
@@ -25,7 +28,12 @@
 Facter.add(:operatingsystem) do
   confine :kernel => :linux
   setcode do
-    if Facter.value(:lsbdistid) == "Ubuntu"
+    if FileTest.exists?("/etc/default/version")
+        txt = File.read("/etc/default/version")
+        if txt =~ /^PRODUCT='(.*?)\s/
+            $1
+        end
+    elsif Facter.value(:lsbdistid) == "Ubuntu"
        "Ubuntu"
     elsif FileTest.exists?("/etc/debian_version")
       "Debian"
EOF

cd /etc/puppet
patch -p0 << EOF
--- puppet.conf 2013-03-21 14:55:43.969130799 -0700
+++ puppet.conf.new 2013-03-21 14:56:02.690178578 -0700
@@ -1,4 +1,6 @@
 [main]
+    server = ""
+    certname = ""
     # The Puppet log directory.
     # The default value is '$vardir/log'.
     logdir = /var/log/puppet
EOF

cd /usr/libexec
patch -p0 << EOF
--- ovirt-init-functions.sh 2013-03-21 15:30:13.078014954 -0700
+++ ovirt-init-functions-new.sh 2013-03-21 16:33:52.893135359 -0700
@@ -223,6 +223,9 @@
     #   rhn_proxyuser=PROXY-USERNAME
     #   rhn_proxypassword=PROXY-PASSWORD
     #   snmp_password=<authpassphrase>
+    #   puppet_enabled=<y|n>
+    #   puppet_server=server
+    #   puppet_cetname=<certname>
 
     #   BOOTIF=link|eth*|<MAC> (appended by pxelinux)
     # network boot interface is assumed to be on management network where
@@ -329,6 +332,14 @@
     cim_passwd=
     cim_enabled=
 
+    # Puppet related options
+    # puppet_enabled=y|n
+    # puppet_server=server
+    # puppet_certname=<certname>
+    puppet_enabled=
+    puppet_server=
+    puppet_certame=
+
     #   pxelinux format: ip=<client-ip>:<boot-server-ip>:<gw-ip>:<netmask>
     #   anaconda format: ip=<client-ip> netmask=<netmask> gateway=<gw-ip>
     #   or               ip=dhcp|off
@@ -613,6 +624,19 @@
             snmp_password=${i#snmp_password=}
             ;;
 
+            puppet_enabled=n | puppet_enabled=0)
+            puppet_enabled=0
+            ;;
+            puppet_enabled* | puppet_enabled=y | puppet_enabled=1)
+            puppet_enabled=1
+            ;;
+            puppet_server=*)
+            puppet_server=${i#puppet_server=}
+            ;;
+            puppet_certname=*)
+            puppet_certname=${i#puppet_certname=}
+            ;;
+
             mem_overcommit* | ovirt_overcommit*)
             i=${i#mem_overcommit=}
             i=${i#ovirt_overcommit=}
@@ -797,7 +821,7 @@
 
 
     # save boot parameters as defaults for ovirt-config-*
-    params="bootif init init_app vol_boot_size vol_efi_size vol_swap_size vol_root_size vol_config_size vol_logging_size vol_data_size vol_swap2_size vol_data2_size crypt_swap crypt_swap2 upgrade standalone overcommit ip_address ip_netmask ip_gateway ipv6 dns ntp vlan ssh_pwauth syslog_server syslog_port collectd_server collectd_port bootparams hostname firstboot rhn_type rhn_url rhn_ca_cert rhn_username rhn_password rhn_profile rhn_activationkey rhn_org rhn_proxy rhn_proxyuser rhn_proxypassword runtime_mode kdump_nfs iscsi_name snmp_password install netconsole_server netconsole_port stateless cim_enabled wipe_fakeraid iscsi_init iscsi_target_name iscsi_target_host iscsi_target_port iscsi_install"
+    params="bootif init init_app vol_boot_size vol_efi_size vol_swap_size vol_root_size vol_config_size vol_logging_size vol_data_size vol_swap2_size vol_data2_size crypt_swap crypt_swap2 upgrade standalone overcommit ip_address ip_netmask ip_gateway ipv6 dns ntp vlan ssh_pwauth syslog_server syslog_port collectd_server collectd_port bootparams hostname firstboot rhn_type rhn_url rhn_ca_cert rhn_username rhn_password rhn_profile rhn_activationkey rhn_org rhn_proxy rhn_proxyuser rhn_proxypassword runtime_mode kdump_nfs iscsi_name snmp_password install netconsole_server netconsole_port stateless cim_enabled wipe_fakeraid iscsi_init iscsi_target_name iscsi_target_host iscsi_target_port iscsi_install puppet_enabled puppet_server puppet_certname"
     # mount /config unless firstboot is forced
     if [ "$firstboot" != "1" ]; then
         mount_config
@@ -855,6 +879,13 @@
         /usr/sbin/usermod -p "$rootpw" root
         chage -d 0 root
     fi
+    if [ "$puppet_enabled" = 1]; then
+        if [ `hostname` != "localhost" ] | [ -n $puppet_certname ]; then
+            python -c "from ovirt.node.setup.puppet_page import *; ActivatePuppet()"  
+        else
+            log "Puppet disabled. Hostname not set and puppet_certname not specified"
+        fi
+    fi
     # check if root or admin password is expired, this might be upon reboot
     # in case of automated installed with rootpw or adminpw parameter!
     if LC_ALL=C chage -l root | grep  -q "password must be changed" \
@@ -1373,8 +1404,6 @@
     return $?
 }
 
-
-
 #
 # If called with a param from .service file:
 #
EOF

%preun

%files recipe
%{recipe_root}

%files
%{python_sitelib}/ovirt/node/setup/puppet_page.py*
%{_localstatedir}/lib/puppet/facts/ovirt.rb

%changelog
* Fri Mar 22 2013 Ryan Barry <rbarry@redhat.com> 0.0.1
- initial commit
