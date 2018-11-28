#!/usr/bin/env python3

import argparse
import logging
import os
import sys

import zaza.utilities.openstack as openstack_utils

logger = logging.getLogger('connectivity_tests')

logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)

def assign_ip(neutron_client, instance_id):
    port = openstack_utils.get_ports_from_device_id(
        neutron_client,
        instance_id)[0]
    logger.debug("Found port for {}".format(instance_id))
    ip = openstack_utils.create_floating_ip(
        neutron_client,
        "ext_net",
        port=port)['floating_ip_address']
    logger.debug("Assigned {} to {}".format(ip, instance_id))
    return ip

def get_priv_key(key_file):
    with open(key_file, 'rt') as f:
        key_data = f.read()
    return key_data


def wait(nova_client, instance_id, vm_name):
    logging.info('Checking instance is active')
    openstack_utils.resource_reaches_status(
        nova_client.servers,
        instance_id,
        expected_status='ACTIVE')

    logging.info('Checking cloud init is complete')
    openstack_utils.cloud_init_complete(
        nova_client,
        instance_id,
        '{} console'.format(vm_name))

def parse_args(args):
    """Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vm-name', help='VM Name',
                        required=True)
    parser.add_argument('-k', '--key-file', help='Private Key file',
                        required=True)
    return parser.parse_args(args)

def main():
    """Cleanup after test run."""
    args = parse_args(sys.argv[1:])

    keystone_session = openstack_utils.get_overcloud_keystone_session()
    nova_client = openstack_utils.get_nova_session_client(keystone_session)
    neutron_client = openstack_utils.get_neutron_session_client(keystone_session)

    instance = nova_client.servers.find(name=args.vm_name)
    logger.debug("Found vm {} with instance is {}".format(args.vm_name,
                                                          instance.id))
    wait(nova_client, instance.id, args.vm_name)
    ip = assign_ip(neutron_client, instance.id)

    logger.debug("Checking ping to {}".format(ip))
    openstack_utils.ping_response(ip)

    logger.debug("Checking ssh to {}".format(ip))
    openstack_utils.ssh_test(
        username='ubuntu',
        ip=ip,
        vm_name=args.vm_name,
        password=None,
        privkey=get_priv_key(args.key_file))

if __name__ == "__main__":
    main()
