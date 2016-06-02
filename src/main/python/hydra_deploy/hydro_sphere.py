#!/usr/bin/python

import os
import argparse
from shell_command import shell_call
from contextlib import contextmanager
import setup_helpers
import ConfigParser


@contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(previous_dir)


def setup(config_file, deployment_id, ssh_key_file):
    mesos_marathon_setup_cmd = "python mesos_marathon_setup.py --config_file " + config_file + \
                               " --deployment_id " + deployment_id + " --ssh_key_file " + ssh_key_file
    shell_call(mesos_marathon_setup_cmd)

    hydra_setup_cmd = "python hydra_setup_script.py --deployment_id " + deployment_id + " --instance_user_name " + \
                      instance_user_name
    shell_call(hydra_setup_cmd)

    mesos_all_ips_list = setup_helpers.get_mesos_all_ips(local_work_dir, deployment_id)
    mesos_masters_ips_list = setup_helpers.get_mesos_masters_ips(local_work_dir, deployment_id)
    mesos_slaves_ips_list = setup_helpers.get_mesos_slaves_ips(local_work_dir, deployment_id)

    print ("*******************************************************************************")
    print ("Hydra on Master node of Mesos cluster has been setup successfully. \n"
           "Master IPs: %s \n" % mesos_masters_ips_list +
           "Slaves IPs: %s \n" % mesos_slaves_ips_list +
           "You can ssh to master using ssh username@masterip")
    print ("*******************************************************************************")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to setup Mesos/Marathon cluster on Google Compute '
                                                 'Engine instances. It will also install Hydra on one of master nodes.')
    parser.add_argument('--config_file', '-f', type=str, default=os.getcwd() + "/setup_config.ini",
                        help='Absolute path of configuration file which dictates the number of master/slave nodes '
                             'along with their machine type. Default is ' + os.getcwd() + '/setup_config.ini .')
    parser.add_argument('--deployment_id', '-i', type=str,
                        help='Each cluster deployment needs to have a unique identifier.'
                             ' This helps in creating multiple deployments in parallel.', required=True)
    parser.add_argument('--ssh_key_file', '-k', type=str, default=os.environ['HOME'] + "/.ssh/id_rsa.pub",
                        help='SSH public key absolute path. It would be used to get passwordless login to cloud '
                             'instances. Default is ~/.ssh/id_rsa.pub')
    # parser.add_argument('--cont', '-t', action='store_true',
    #                    help='If your script fails because of any reason in middle of somethhing, use this flag. '
    #                         'This flag will resume the script from failed step. ')

    parser.add_argument('--clean', '-c', action='store_true', help='cleanup instances')
    args = parser.parse_args()

    ssh_key_file = args.ssh_key_file
    config_file = args.config_file
    deployment_id = args.deployment_id
    local_work_dir = os.environ['HOME']

    config = ConfigParser.ConfigParser()
    config.read(config_file)
    sections = config.sections()
    instance_user_name = setup_helpers.get_setting_val(config, "instanceusername")

    if args.clean:
        # TODO: Needs to be updated. This should be a function and should clean the instances according to supplied tag.
        print("==> Removing deployment nodes")
        f = open(local_work_dir + '/.' + deployment_id + '_mesos_all_ips', 'r')
        for ip in f:
            ip = ip.rstrip()
            setup_helpers.delete_instance(config, ip)
        shell_call("rm " + local_work_dir + "/." + deployment_id + "_mesos_all_ips")
        shell_call("rm " + local_work_dir + "/." + deployment_id + "_mesos_masters_ips")
        shell_call("rm " + local_work_dir + "/." + deployment_id + "_mesos_slaves_ips")
    else:
        setup(config_file, deployment_id, ssh_key_file)
