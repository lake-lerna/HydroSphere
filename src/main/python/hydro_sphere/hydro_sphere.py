#!/usr/bin/python
import os
import argparse
import re
from exceptions import ValueError

from config import Config
from deployment import Deployment


parser = argparse.ArgumentParser(description='Script to setup Mesos/Marathon cluster on Google Compute '
                                             'Engine instances. It will also install Hydra on one of master nodes.')
parser.add_argument('--config_file', '-f', type=str, default=os.getcwd() + "/setup_config.ini",
                    help='Absolute path of configuration file which dictates the number of master/slave nodes '
                         'along with their machine type. Default is ' + os.getcwd() + '/setup_config.ini .')
parser.add_argument('--deployment_id', '-i', type=str,
                    help='Each cluster deployment needs to have a unique identifier.'
                         ' This helps in creating multiple deployments in parallel.', required=True)
parser.add_argument('--start', '-r', type=int, default=1, help='start step')
parser.add_argument('--end', '-e', type=int, default=16, help='end step')
parser.add_argument('--clean', '-c', action='store_true', help='cleanup instances')
args = parser.parse_args()


def validate_deployment_id(deployment_id):
    # Since hydra depends on dashes and gce api doesn't allow other non-aphanumeric characters
    # in instance names, don't allow them in deployment_ids
    if re.match(r"^[a-z0-9]+$", deployment_id):
        return deployment_id
    else:
        exception_msg = "--deployment_id | -i <%s> cannot contain non-alphanumeric characters" % (deployment_id)
        raise ValueError(exception_msg)


if __name__ == "__main__":
    deployment_id = validate_deployment_id(args.deployment_id)
    config_file = args.config_file

    config = Config(deployment_id)
    config.parse_config_file(config_file)  # Will populate config section list of config.
    dep = Deployment(config)

    if args.clean:
        print("==> Removing deployment nodes for deployment-id: %s" % deployment_id)
        dep.cleanup()
    else:
        for step in range(args.start, args.end + 1):
            print ("======================= STEP %d =======================" % step)
            dep.deploy(step)
