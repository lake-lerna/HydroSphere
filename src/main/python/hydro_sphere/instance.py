#!/usr/bin/python
from shell_command import shell_call
import socket
import time
import subprocess
from fabric.api import put, run, settings, sudo


class Instance(object):
    def __init__(self, name, disk_list, machine_type, user_name):
        self.name = name
        self.disk_list = disk_list
        self.machine_type = machine_type
        self.user_name = user_name
        self.ip = None

    def create(self, common_section):
        pathname = "/tmp/gce_key.txt"

        tfile = open(pathname, 'w')
        with open(common_section.sshkey) as f:
            lines = f.readlines()
            tfile.writelines(self.user_name + ":" + lines[0])
        tfile.close()

        cmd = "gcloud compute instances create " + self.name + " --machine-type " + self.machine_type + \
              " --network " + common_section.network + \
              " --maintenance-policy MIGRATE --scopes https://www.googleapis.com/auth/cloud-platform " \
              "--disk name=" + self.disk_list[0].name + ",mode=rw,boot=yes,auto-delete=yes --disk name=" + \
              self.disk_list[1].name + \
              ",mode=rw,boot=no,auto-delete=yes --no-address --tags no-ip --metadata-from-file sshKeys=" + pathname
        print("create_instance_cmd = %s" % cmd)
        shell_call(cmd)
        self.ip = self.get_ip()
        return self.ip

    def delete(self, common_section):
        common_section.compute.instances().delete(project=common_section.project, zone=common_section.zone,
                                                  instance=self.name).execute()

    def is_ready(self, num_retries=10):
        original_timeout = socket.getdefaulttimeout()
        new_timeout = 10
        delay = 3
        socket.setdefaulttimeout(new_timeout)
        host_status = False
        for retry in range(num_retries):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self.ip, 22))
                host_status = True
                print ("%s (%s) is ready" % (self.name, self.ip))
                break
            except socket.error as e:
                print("Error on connect to %s (%s): %s" % (self.name, self.ip, e))
            s.close()
            time.sleep(delay)
        socket.setdefaulttimeout(original_timeout)
        return host_status

    @staticmethod
    def __run_shell_cmd(command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        return output

    def get_ip(self):
        command = "gcloud compute instances list | grep -w " + self.name
        # tahir-deploymentid-section-tag-0 us-central1-f n1-standard-4 10.10.0.28 RUNNING
        output = self.__run_shell_cmd(command)
        ip = output.split()[3]  # 10.10.0.28
        return ip

    def get_file(self, src_pathname, dst_path, use_sudo=False):
        with settings(host_string=self.ip, user=self.user_name):
            if use_sudo:
                put(src_pathname, dst_path, use_sudo=True)
            else:
                put(src_pathname, dst_path)

    def run_cmd(self, cmd, use_sudo=False, forward_agent=False):
            with settings(host_string=self.ip, user=self.user_name, forward_agent=forward_agent):
                if use_sudo:
                    sudo(cmd)
                else:
                    run(cmd)

    # This function makes sense only when instance name is of form <emailid>-<deploymentid>-<configsection>-<tag>-<num>.
    def get_instance_tag_and_num(self):
        tag_lst = self.name.split("-")[3:-1]
        tag = "-".join(tag_lst)
        instance_number = self.name.split("-")[-1:]  # 0
        return (tag, instance_number[0])
