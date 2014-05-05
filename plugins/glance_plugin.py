#!/usr/bin/env python
#
# vim: tabstop=4 shiftwidth=4

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# Authors:
#   Ricardo Rocha <ricardo@catalyst.net.nz>
#
# About this plugin:
#   This plugin collects OpenStack glance information, including number
#   of images and bytes used per tenant.
#
# collectd:
#   http://collectd.org
# OpenStack Glance:
#   http://docs.openstack.org/developer/glance/
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml
#
from keystoneclient.v2_0 import Client as KeystoneClient
from glanceclient.v2.client import Client as GlanceClient

import collectd
from common import Helper

global HELPER

HELPER = Helper()

def get_stats(user, passwd, tenant, url, host=None):
    """Retrieves images stats from glance"""
    keystone = KeystoneClient(username=user, password=passwd, tenant_name=tenant, auth_url=url)

    # Find my uuid
    user_list = keystone.users.list()
    admin_uuid = ""
    for usr in user_list:
        if usr.name == user:
            admin_uuid = usr.id

    # Find out which tenants I have roles in
    tenant_list = keystone.tenants.list()
    my_tenants = list()
    for tenant in tenant_list:
        if keystone.users.list_roles(user=admin_uuid, tenant=tenant.id):
            my_tenants.append( { "name": tenant.name, "id": tenant.id } )

    data = { HELPER.prefix: {} }
    glance_endpoint = keystone.service_catalog.url_for(service_type='image')
    for tenant in my_tenants:
        client = GlanceClient(glance_endpoint, token=keystone.auth_token)

        data[HELPER.prefix][tenant['name']] = { 'images': {} }
        data_tenant = data[HELPER.prefix][tenant['name']]
        data_tenant['images']['count'] = 0
        data_tenant['images']['bytes'] = 0

        image_list = client.images.list()
        for image in image_list:
            data_tenant['images']['count'] += int(images['size'])
            data_tenant['images']['bytes'] += int(images['size'])
            
    return data

def configure_callback(conf):
    """Received configuration information"""
    HELPER.config(conf, 'openstack-glance')

def read_callback():
    """Callback to read values and dispatch"""
    stats = get_stats(HELPER.username, HELPER.password, HELPER.tenant, HELPER.auth_url)
    HELPER.dispatch(stats)


collectd.register_config(configure_callback)
collectd.info("%s: initializing plugin" % HELPER.prefix)
collectd.register_read(read_callback)
