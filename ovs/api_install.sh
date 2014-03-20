#!/bin/bash

# 1. update first
apt-get update

# 2. install packages
# install neutron server and client and assume rabbitmq is on another host
apt-get install -y neutron-server python-neutronclient

# install ovs plugin
apt-get install -y neutron-plugin-openvswitch

# install mysql tools, assume mysql server is on another host
apt-get install -y python-mysqldb python-sqlalchemy

# 3. configure neutron-server
# source setting
. settingrc

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

