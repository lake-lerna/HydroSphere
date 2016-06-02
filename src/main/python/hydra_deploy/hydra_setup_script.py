#!/usr/bin/python
import os
import argparse
import setup_helpers
import ntpath
from shell_command import shell_call


# TODO: Check whether IPs files exist?
def setup(step):
    if step == 1:
        print("==> Clone hydra on master node")
        setup_helpers.run_cmd_on_host(instance_user_name, mesos_masters_ips_list[0], "sudo apt-get -y install git unzip")
        setup_helpers.run_cmd_on_host(instance_user_name, mesos_masters_ips_list[0],
                                      "wget https://github.com/sushilks/hydra/archive/master.zip && unzip master.zip")

    elif step == 2:
        print("==> Add grouping to slaves so that you can steer the workload")
        script_path_name = os.getcwd() + "/vm_files/add_grouping.sh"
        script_name = ntpath.basename(script_path_name)

        print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
        setup_helpers.upload_to_multiple_hosts(instance_user_name, mesos_slaves_ips_list, script_path_name, dst_work_dir)

        f = open(local_work_dir + '/.' + deployment_id + '_mesos_slaves_ips', 'r')
        for ip in f:
            ip = ip.strip()
            instance_tag = setup_helpers.get_instance_tag(ip)
            setup_helpers.run_cmd_on_host(instance_user_name, ip,
                                          "/bin/bash " + dst_work_dir + "/" + script_name + " " + instance_tag)

    elif step == 3:
        print("==> Upload conf file")
        script_path_name = setup_helpers.create_hydra_conf(mesos_masters_ips_list[0])
        script_name = ntpath.basename(script_path_name)

        print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
        setup_helpers.upload_to_host(instance_user_name, mesos_masters_ips_list[0],
                                     script_path_name, dst_work_dir + "/hydra-master")

    elif step == 4:
        print("==> Install packages for hydra on master")
        script_path_name = os.getcwd() + "/vm_files/hydra_pkgs_install.sh"
        script_name = ntpath.basename(script_path_name)

        print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
        setup_helpers.upload_to_multiple_hosts(instance_user_name, mesos_masters_ips_list, script_path_name, dst_work_dir)

        print("==> Running %s/%s script" % (dst_work_dir, script_name))
        setup_helpers.run_cmd_on_multiple_hosts(instance_user_name, mesos_masters_ips_list,
                                                "/bin/bash " + dst_work_dir + "/" + script_name + " " + dst_work_dir)

    elif step == 5:
        print("==> Install packages for hydra on slave")
        setup_helpers.run_cmd_on_multiple_hosts(
            instance_user_name, mesos_slaves_ips_list,
            "apt-get install -y python-dev python-pip libtool pkg-config build-essential autoconf automake",
            use_sudo=True)
        print("==> Install libzmq3-dev")
        setup_helpers.run_cmd_on_multiple_hosts(
            instance_user_name, mesos_slaves_ips_list,
            "sudo add-apt-repository ppa:chris-lea/zeromq -y && sudo apt-get update "
            "&& sudo apt-get install -y libzmq3-dev",
            use_sudo=True)
        print("==> pip install psutil pyzmq protobuf pika")
        setup_helpers.run_cmd_on_multiple_hosts(instance_user_name, mesos_slaves_ips_list,
                                                "pip install psutil pyzmq protobuf pika", use_sudo=True)

if __name__ == "__main__":
    default_start_step = 1
    default_end_step = 5

    parser = argparse.ArgumentParser(description='Hydra setup script')
    parser.add_argument('--deployment_id', '-i', type=str,
                        help='Each cluster deployment needs to have a unique identifier. '
                             'This will help in identifying various deployments.', required=True)
    parser.add_argument('--cont', '-t', action='store_true',
                        help='If your script fails because of any reason in middle of somethhing, use this flag. '
                             'This flag will resume the script from failed step. ')
    parser.add_argument('--instance_user', '-u', action='store_true',
                        help='User name of cloud instances.')

    parser.add_argument('--start', '-r', type=int, default=default_start_step, help='start step')
    parser.add_argument('--end', '-e', type=int, default=default_end_step, help='end step')
    args = parser.parse_args()

    deployment_id = args.deployment_id
    local_work_dir = os.environ['HOME']
    dst_work_dir = "/home/" + os.environ['USER']
    instance_user_name = args.instance_user
    end_step = args.end

    step_file = local_work_dir + '/.' + deployment_id + '_hydra_setup_script_step'
    # If continue is true
    if args.cont:
        start_step = int(setup_helpers.read_str_from_file(step_file)) + 1
        print("continue is given. start_step=%d" % start_step)
    else:
        start_step = args.start

    mesos_all_ips_list = setup_helpers.get_mesos_all_ips(local_work_dir, deployment_id)
    mesos_masters_ips_list = setup_helpers.get_mesos_masters_ips(local_work_dir, deployment_id)
    mesos_slaves_ips_list = setup_helpers.get_mesos_slaves_ips(local_work_dir, deployment_id)

    for step in range(start_step, end_step + 1):
        print("******************* starting step %d ***********************" % step)
        setup(step)

        setup_helpers.write_to_file(step_file, str(step))
        if step == default_end_step:
            # Remove step file
            cmd = "rm " + step_file
            shell_call(cmd)
