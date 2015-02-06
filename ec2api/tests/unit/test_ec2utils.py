# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import mock
import testtools

from ec2api.api import ec2utils
from ec2api import exception
from ec2api.tests.unit import fakes
from ec2api.tests.unit import matchers


class EC2UtilsTestCase(testtools.TestCase):

    @mock.patch('ec2api.db.api.IMPL')
    def test_get_db_item(self, db_api):
        item = {'fake_key': 'fake_value'}
        db_api.get_item_by_id.return_value = item

        def check_normal_flow(kind, ec2_id):
            item['id'] = ec2_id
            res = ec2utils.get_db_item('fake_context', kind, ec2_id)
            self.assertThat(res, matchers.DictMatches(item))
            db_api.get_item_by_id.assert_called_once_with('fake_context',
                                                          kind, ec2_id)
            db_api.reset_mock()

        check_normal_flow('vpc', 'vpc-001234af')
        check_normal_flow('igw', 'igw-00000022')

        def check_not_found(kind, ex_class):
            ec2_id = fakes.random_ec2_id(kind)
            self.assertRaises(ex_class,
                              ec2utils.get_db_item,
                              'fake_context', kind, ec2_id)
            db_api.get_item_by_id.assert_called_once_with('fake_context',
                                                          kind, ec2_id)
            db_api.reset_mock()

        db_api.get_item_by_id.return_value = None
        check_not_found('vpc', exception.InvalidVpcIDNotFound)
        check_not_found('igw', exception.InvalidInternetGatewayIDNotFound)
        check_not_found('subnet', exception.InvalidSubnetIDNotFound)
        check_not_found('eni', exception.InvalidNetworkInterfaceIDNotFound)
        check_not_found('dopt', exception.InvalidDhcpOptionsIDNotFound)
        check_not_found('eipalloc', exception.InvalidAllocationIDNotFound)
        check_not_found('sg', exception.InvalidGroupNotFound)
        check_not_found('rtb', exception.InvalidRouteTableIDNotFound)
        check_not_found('i', exception.InvalidInstanceIDNotFound)
        check_not_found('vol', exception.InvalidVolumeNotFound)
        check_not_found('snap', exception.InvalidSnapshotNotFound)
        check_not_found('ami', exception.InvalidAMIIDNotFound)
        check_not_found('ari', exception.InvalidAMIIDNotFound)
        check_not_found('aki', exception.InvalidAMIIDNotFound)

    @mock.patch('ec2api.db.api.IMPL')
    def test_get_db_items(self, db_api):
        items = [{'id': fakes.random_ec2_id('fake'),
                  'fake_key': 'fake_value'},
                 {'id': fakes.random_ec2_id('fake'),
                  'fake_key': 'fake_value'}]
        db_api.get_items.return_value = items
        db_api.get_items_by_ids.return_value = items

        def check_with_no_filter(empty_filter):
            res = ec2utils.get_db_items('fake_context', 'fake', empty_filter)
            self.assertThat(res, matchers.ListMatches(items))
            db_api.get_items.assert_called_once_with('fake_context', 'fake')
            db_api.reset_mock()

        check_with_no_filter(None)
        check_with_no_filter([])

        def check_with_filter(item_ids):
            res = ec2utils.get_db_items('fake_context', 'fake', item_ids)
            self.assertThat(res, matchers.ListMatches(items))
            db_api.get_items_by_ids.assert_called_once_with(
                'fake_context', 'fake', set(item_ids))
            db_api.reset_mock()

        item_ids = [i['id'] for i in items]
        check_with_filter(item_ids)
        check_with_filter(item_ids * 2)

        def check_not_found(kind, ex_class):
            items = [{'id': fakes.random_ec2_id(kind),
                      'fake_key': 'fake_value'} for _ in range(2)]
            item_ids = [i['id'] for i in items]
            item_ids.append(fakes.random_ec2_id(kind))
            db_api.get_items_by_ids.return_value = items
            self.assertRaises(ex_class, ec2utils.get_db_items,
                              'fake_context', kind, item_ids)
            db_api.reset_mock()

        check_not_found('vpc', exception.InvalidVpcIDNotFound)
        check_not_found('igw', exception.InvalidInternetGatewayIDNotFound)
        check_not_found('subnet', exception.InvalidSubnetIDNotFound)
        check_not_found('eni', exception.InvalidNetworkInterfaceIDNotFound)
        check_not_found('dopt', exception.InvalidDhcpOptionsIDNotFound)
        check_not_found('eipalloc', exception.InvalidAllocationIDNotFound)
        check_not_found('sg', exception.InvalidGroupNotFound)
        check_not_found('rtb', exception.InvalidRouteTableIDNotFound)
        check_not_found('i', exception.InvalidInstanceIDNotFound)
        check_not_found('vol', exception.InvalidVolumeNotFound)
        check_not_found('snap', exception.InvalidSnapshotNotFound)
        check_not_found('ami', exception.InvalidAMIIDNotFound)
        check_not_found('aki', exception.InvalidAMIIDNotFound)
        check_not_found('ari', exception.InvalidAMIIDNotFound)

    """Unit test api xml conversion."""
    def test_number_conversion(self):
        conv = ec2utils._try_convert
        self.assertIsNone(conv('None'))
        self.assertEqual(conv('True'), True)
        self.assertEqual(conv('TRUE'), True)
        self.assertEqual(conv('true'), True)
        self.assertEqual(conv('False'), False)
        self.assertEqual(conv('FALSE'), False)
        self.assertEqual(conv('false'), False)
        self.assertEqual(conv('0'), 0)
        self.assertEqual(conv('42'), 42)
        self.assertEqual(conv('3.14'), 3.14)
        self.assertEqual(conv('-57.12'), -57.12)
        self.assertEqual(conv('0x57'), 0x57)
        self.assertEqual(conv('-0x57'), -0x57)
        self.assertEqual(conv('-'), '-')
        self.assertEqual(conv('-0'), 0)
        self.assertEqual(conv('0.0'), 0.0)
        self.assertEqual(conv('1e-8'), 0.0)
        self.assertEqual(conv('-1e-8'), 0.0)
        self.assertEqual(conv('0xDD8G'), '0xDD8G')
        self.assertEqual(conv('0XDD8G'), '0XDD8G')
        self.assertEqual(conv('-stringy'), '-stringy')
        self.assertEqual(conv('stringy'), 'stringy')
        self.assertEqual(conv('add'), 'add')
        self.assertEqual(conv('remove'), 'remove')
        self.assertEqual(conv(''), '')
