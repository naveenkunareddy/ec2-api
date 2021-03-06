# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from rally.common.i18n import _
from rally.common import log as logging
from rally.common import utils as rutils
from rally import consts
from rally import osclients
from rally.plugins.openstack.wrappers import network as network_wrapper
from rally.task import context


LOG = logging.getLogger(__name__)


@context.configure(name="prepare_ec2_client", order=110)
class PrepareEC2ClientContext(context.Context):

    def __init__(self, ctx):
        super(PrepareEC2ClientContext, self).__init__(ctx)
        self.net_wrapper = network_wrapper.wrap(
            osclients.Clients(self.context["admin"]["credential"]),
            self, config=self.config)
        self.net_wrapper.start_cidr = '10.0.0.0/16'

    @logging.log_task_wrapper(LOG.info, _("Enter context: `EC2 creds`"))
    def setup(self):
        """This method is called before the task start."""
        try:
            for user in self.context['users']:
                osclient = osclients.Clients(user['credential'])
                keystone = osclient.keystone()
                creds = keystone.ec2.list(user['id'])
                if not creds:
                    creds = keystone.ec2.create(user['id'], user['tenant_id'])
                else:
                    creds = creds[0]
                url = 'http://192.168.100.49:8788/services/Cloud'
                url_parts = url.rpartition(':')
                nova_url = (url_parts[0] + ':8773/'
                            + url_parts[2].partition('/')[2])
                user['ec2args'] = {
                    'region': 'RegionOne',
                    'url': url,
                    'nova_url': nova_url,
                    'access': creds.access,
                    'secret': creds.secret
                }

#            if self.net_wrapper.SERVICE_IMPL == consts.Service.NEUTRON:
#                for user, tenant_id in rutils.iterate_per_tenants(
#                        self.context["users"]):
#                    body = {"quota": {"router": -1, "floatingip": -1}}
#                    self.net_wrapper.client.update_quota(tenant_id, body)
#                    network = self.net_wrapper.create_network(
#                        tenant_id, add_router=True, subnets_num=1)
#                    self.context["tenants"][tenant_id]["network"] = network

        except Exception as e:
            msg = "Can't prepare ec2 client: %s" % e.message
            if logging.is_debug():
                LOG.exception(msg)
            else:
                LOG.warning(msg)

    @logging.log_task_wrapper(LOG.info, _("Exit context: `EC2 creds`"))
    def cleanup(self):
        try:
            #if self.net_wrapper.SERVICE_IMPL == consts.Service.NEUTRON:
            #        network = self.context["tenants"][tenant_id]["network"]
            #       self.net_wrapper.delete_network(network)
            print 'clenaup'
        except Exception as e:
            msg = "Can't cleanup ec2 client: %s" % e.message
            if logging.is_debug():
                LOG.exception(msg)
            else:
                LOG.warning(msg)

