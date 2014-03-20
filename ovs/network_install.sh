#!/bin/bash

# 1. update first
apt-get update
# source setting
. settingrc

# 2. install packages
# install neutron dhcp and l3 agent, metadata-agent
apt-get install -y neutron-dhcp-agent neutron-l3-agent neutron-metadata-agent

# install ovs plugin and agent
apt-get install -y neutron-plugin-openvswitch neutron-plugin-openvswitch-agent openvswitch-switch openvswitch-datapath-dkms ethtool

# install mysql tools, assume mysql server is on another host
apt-get install -y python-mysqldb python-sqlalchemy

# enable ip forwarding
echo -e "net.ipv4.ip_forward=1\n\
net.ipv4.conf.all.rp_filter=0\n\
net.ipv4.conf.default.rp_filter=0">> /etc/sysctl.conf
sysctl -p

# disable gro
ethtool -K $DEV_EXT gro off

# 3. configure neutron-server
/etc/init.d/openvswitch-switch restart
ovs-vsctl add-br br-ex
ovs-vsctl add-br br-int
ovs-vsctl add-port br-ex $DEV_EXT
ip=`ip addr show dev $DEV_EXT | sed -nr 's/.*inet ([^ ]+).*/\1/p'`
ip addr del $ip dev $DEV_EXT
ip add add $ip dev br-ex
/etc/init.d/networking restart

# neutron.conf
sed -i "s/# debug = False/debug = True/g" /etc/neutron/neutron.conf
sed -i "s/# allow_overlapping_ips = False/allow_overlapping_ips = True/g" /etc/neutron/neutron.conf
sed -i "s/# rabbit_host = localhost/rabbit_host = rabbitmq_vip/g" /etc/neutron/neutron.conf
sed -i "s/# rabbit_password = guest/rabbit_password = $RABBIT_PASS/g" /etc/neutron/neutron.conf

sed -i "s/# quota_port = 50/quota_port = 500/g" /etc/neutron/neutron.conf

sed -i "s/auth_host = 127.0.0.1/auth_host = $AUTH_HOST/g" /etc/neutron/neutron.conf
sed -i "s/%SERVICE_TENANT_NAME%/$SERVICE_TENANT_NAME/g" /etc/neutron/neutron.conf
sed -i "s/%SERVICE_USER%/$SERVICE_USER/g" /etc/neutron/neutron.conf
sed -i "s/%SERVICE_PASSWORD%/$SERVICE_PASSWORD/g" /etc/neutron/neutron.conf

sed -i "s|connection = sqlite:////var/lib/neutron/neutron.sqlite|connection = mysql://neutron:$MYSQL_PASS@mysql_vip:3306/neutron|g" /etc/neutron/neutron.conf

# dhcp
echo -e "# overrided by xiaolin\n\
ovs_use_veth = True\n\
use_namespaces = True\n\
dhcp_domain = cc\n\
interface_driver = neutron.agent.linux.interface.OVSInterfaceDriver">> /etc/neutron/dhcp_agent.ini

# l3
echo -e "# overrided by xiaolin\n\
ovs_use_veth = True\n\
use_namespaces = True\n\
handle_internal_only_routers = False\n\
interface_driver = neutron.agent.linux.interface.OVSInterfaceDriver">> /etc/neutron/l3_agent.ini

# metadata
sed -i "s/# debug = False/debug = True/g" /etc/neutron/metadata_agent.ini
sed -i "s/localhost/$AUTH_HOST/g" /etc/neutron/metadata_agent.ini
sed -i "s/RegionOne/$REGION/g" /etc/neutron/metadata_agent.ini
sed -i "s/%SERVICE_TENANT_NAME%/$SERVICE_TENANT_NAME/g" /etc/neutron/metadata_agent.ini
sed -i "s/%SERVICE_USER%/$SERVICE_USER/g" /etc/neutron/metadata_agent.ini
sed -i "s/%SERVICE_PASSWORD%/$SERVICE_PASSWORD/g" /etc/neutron/metadata_agent.ini
sed -i "s/# nova_metadata_ip = 127.0.0.1/nova_metadata_ip = nova_vip/g" /etc/neutron/metadata_agent.ini
sed -i "s/# metadata_proxy_shared_secret =/metadata_proxy_shared_secret = $METADATA_PASS/g" /etc/neutron/metadata_agent.ini

# ovs_agent
LOCAL_IP=`ip addr show dev $DEV_INT | sed -nr 's/.*inet ([^ ]+).*/\1/p' | awk -F'/' '{print $1}'`
echo -e "[database]\n\
connection = mysql://neutron:$MYSQL_PASS@mysql_vip:3306/neutron\n\n\
[OVS]\n\
tenant_network_type = gre\n\
tunnel_id_ranges = 1:10000\n\
enable_tunneling = True\n\
integration_bridge = br-int\n\
tunnel_bridge = br-tun\n\
local_ip = $LOCAL_IP\n\n\
[SECURITYGROUP]\n\
firewall_driver = neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver">> /etc/neutron/plugins/openvswitch/ovs_neutron_plugin.ini

# restart services
cd /etc/init.d;for i in `ls neutron-*`;do service $i restart;done;cd -

# echo
echo "Please modify network/interfaces manually, then set up ha."

