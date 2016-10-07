#!/usr/bin/python
from disk import Disk
from instance import Instance
import os
import ntpath
from tempfile import mkstemp


class Deployment(object):
    def __init__(self, config):
        self.config = config
        self.master_instances = list()
        self.slave_instances = list()
        self.instances = list()
        self.masters_ips_list = None
        self.slaves_ips_list = None
        self.all_ips_list = None

    def deploy(self, step):
        # Get configuration setting
        dep_id = self.config.deployment_id
        common_section = self.config.config_sections[0]
        config_sections = self.config.config_sections[1:]
        dst_work_dir = "/home/" + common_section.instance_user_name
        # self.debug()

        if step == 1:
            # Create Instances
            print ("==> Create master and slave nodes <==")
            self.__create_instances(dep_id, common_section, config_sections)

        elif step == 2:
            # Populate master and slaves IP list. It will help us in performaing operations on master and slaves.
            print ("==> Populate master and slaves IP list <==")
            self.masters_ips_list = self.get_nodes_ips_list("master")
            self.slaves_ips_list = self.get_nodes_ips_list("slave")
            self.all_ips_list = self.masters_ips_list + self.slaves_ips_list
            print ("master:%s, slaves:%s" % (self.masters_ips_list, self.slaves_ips_list))

        # ******************************* Install Mesos Sphere on the servers. ********************************
        elif step == 3:
            print ("==> Add Mesosphere repository to resources list of ALL hosts  <==")
            # Check if instances up and ready?
            for instance in self.instances:
                instance.is_ready()

            script_path_name = os.getcwd() + "/vm_files/add_mesos_sphere_repo_and_install_java.sh"
            script_name = ntpath.basename(script_path_name)

            print("==> Uploading %s" % script_path_name)
            self.upload_to_multiple_instances(self.instances, script_path_name, dst_work_dir)

            print("==> Running /home/%s/%s script" % (common_section.instance_user_name, script_name))
            self.run_cmd_on_multiple_instances(self.instances,
                                               "/bin/bash " + dst_work_dir + "/" + script_name)

        elif step == 4:
            print("==> On master hosts, install mesos and marathon package")
            self.run_cmd_on_multiple_instances(self.master_instances, "sudo apt-get install -y mesos marathon")

            # For your slave hosts, you only need the mesos package, which also pulls in zookeeper as a dependency:
            print("==> On slave hosts, install mesos package")
            self.run_cmd_on_multiple_instances(self.slave_instances, "sudo apt-get -y install mesos")

        elif step == 5:
            # configure our zookeeper connection info. This is the underlying layer that allows all of our hosts to
            # connect to the correct master servers.
            print("==> configure zookeepr connection info")
            config = "zk://"
            for ip in self.masters_ips_list:
                config += ip + ":2181,"
            config = config[:-1] + "/mesos"

            self.run_cmd_on_multiple_instances(self.instances, "echo '" + config + "' > /etc/mesos/zk",
                                               use_sudo=True)

        # ******************************* Master Servers' Zookeeper Configuration ********************************
        # On master servers, we will need to do some additional zookeeper configuration.
        # The first step is to define a unique ID number, from 1 to 255, for each of your master servers.
        # This is kept in the /etc/zookeeper/conf/myid file.
        # we'll specify the hostname and IP address for each of our master servers. We will be using the IP address for
        # the hostname so that our instances will not have trouble resolving correctly
        elif step == 6:
            i = 1
            for instance in self.master_instances:
                instance.run_cmd("echo " + str(i) + " > /etc/zookeeper/conf/myid", use_sudo=True)
                i += 1

        elif step == 7:
            # we need to modify our zookeeper configuration file to map our zookeeper IDs to actual hosts. This will
            # ensure that the service can correctly resolve each host from the ID system that it uses.
            config = ""
            i = 1
            for ip in self.masters_ips_list:
                config += "server." + str(i) + "=" + ip + ":2888:3888\n"
                i += 1
            script_path_name = self.create_zk_conf_script(config)

            print("==> Uploading %s to /etc/zookeeper/conf/" % script_path_name)
            self.upload_to_multiple_instances(self.master_instances, script_path_name, "/etc/zookeeper/conf/",
                                              use_sudo=True)

        # ******************************* Master Servers' Mesos Configuration ********************************
        elif step == 8:
            # TODO: Calculate quoram value
            # quoram_num = (num_masters // 2) + 1
            self.run_cmd_on_multiple_instances(self.master_instances, "echo 1 > /etc/mesos-master/quorum",
                                               use_sudo=True)
            for instance in self.master_instances:
                instance.run_cmd("echo " + instance.ip + " > /etc/mesos-master/ip", use_sudo=True)
                instance.run_cmd("echo " + instance.ip + " > /etc/mesos-master/hostname", use_sudo=True)

        # ******************************* Master Servers' Marathon Configuration ********************************
        elif step == 9:
            print("==> Configuring Master server's Marathon configuration")
            script_path_name = os.getcwd() + "/vm_files/master_marathon_conf.sh"
            script_name = ntpath.basename(script_path_name)

            print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
            self.upload_to_multiple_instances(self.master_instances, script_path_name, dst_work_dir)

            print("==> Running %s/%s script" % (dst_work_dir, script_name))
            self.run_cmd_on_multiple_instances(self.master_instances, "/bin/bash " + dst_work_dir + "/" + script_name)

        # **************************** Configure Service Init Rules and Restart Services ***************************
        elif step == 10:
            print("==> Configuring Service init rules and Restart Services")
            script_path_name = os.getcwd() + "/vm_files/srv_init_rules_and_restart_srv.sh"
            script_name = ntpath.basename(script_path_name)

            print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
            self.upload_to_multiple_instances(self.master_instances, script_path_name, dst_work_dir)

            print("==> Running %s/%s script" % (dst_work_dir, script_name))
            self.run_cmd_on_multiple_instances(self.master_instances, "/bin/bash " + dst_work_dir + "/" + script_name)

        # ###########################################################################################################
        #                                               SLAVE NODEs setup
        # ###########################################################################################################
        elif step == 11:
            print("==> Configuring slave nodes")
            for instance in self.slave_instances:
                script_path_name = self.create_slave_conf_script(instance.ip)
                script_name = ntpath.basename(script_path_name)

                print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
                instance.get_file(script_path_name, dst_work_dir)

                print("==> Running %s/%s script" % (dst_work_dir, script_name))
                instance.run_cmd("/bin/bash " + dst_work_dir + "/" + script_name)
            print("***************************************************************************************************")
            print("Mesos Cluster setup has been completed successfully. \n"
                  "Master IPs = %s \n"
                  "Slave  IPS = %s" % (self.masters_ips_list, self.slaves_ips_list))
            print("***************************************************************************************************")

        elif step == 12:
            print("==> Clone hydra on master node")
            hydra_instance = self.master_instances[0]
            hydra_instance.run_cmd("sudo apt-get -y install git unzip", use_sudo=True)
            # TODO(Muaaz): builder/corelib_hydra.py needs to be updated to use "git clone" for pipeline.
            # hydra_instance.run_cmd("git clone git@github.com:lake-lerna/hydra.git hydra-master", forward_agent=True)
            hydra_instance.run_cmd("wget https://github.com/lake-lerna/hydra/archive/master.zip && unzip master.zip")

        elif step == 13:
            print("==> Add grouping to slaves so that you can steer the workload")
            script_path_name = os.getcwd() + "/vm_files/add_grouping.sh"
            script_name = ntpath.basename(script_path_name)

            print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
            self.upload_to_multiple_instances(self.slave_instances, script_path_name, dst_work_dir)

            for instance in self.slave_instances:
                instance_tag, instance_num = instance.get_instance_tag_and_num()
                instance.run_cmd("/bin/bash " + dst_work_dir + "/" + script_name + " " + instance_tag +
                                 " " + instance_num)

        elif step == 14:
            print("==> Upload conf file")
            hydra_instance = self.master_instances[0]
            script_path_name = self.create_hydra_conf(hydra_instance.ip, len(self.slaves_ips_list))
            script_name = ntpath.basename(script_path_name)

            print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
            hydra_instance.get_file(script_path_name, dst_work_dir + "/hydra-master")

        elif step == 15:
            print("==> Install packages for hydra on master")
            hydra_instance = self.master_instances[0]
            script_path_name = os.getcwd() + "/vm_files/hydra_pkgs_install.sh"
            script_name = ntpath.basename(script_path_name)

            print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
            hydra_instance.get_file(script_path_name, dst_work_dir)

            print("==> Running %s/%s script" % (dst_work_dir, script_name))
            hydra_instance.run_cmd("/bin/bash " + dst_work_dir + "/" + script_name + " " + dst_work_dir)

        elif step == 16:
            print("==> Installing required Hydra packages on slaves")
            script_path_name = os.getcwd() + "/vm_files/hydra_pkgs_install_slaves.sh"
            script_name = ntpath.basename(script_path_name)

            print("==> Uploading %s to %s" % (script_path_name, dst_work_dir))
            self.upload_to_multiple_instances(self.slave_instances, script_path_name, dst_work_dir)

            print("==> Running %s/%s script" % (dst_work_dir, script_name))
            self.run_cmd_on_multiple_instances(self.slave_instances, "/bin/bash " + dst_work_dir + "/" + script_name)

        elif step == 17:
            print("==> Copying master public key to authorized key of all slaves")
            master_instance = self.master_instances[0]
            pub_key = master_instance.run_cmd("cat ~/.ssh/id_rsa.pub", use_sudo=True)
            self.append_to_file_on_multiple_instances(self.slave_instances,
                                                      "~/.ssh/authorized_keys",
                                                      pub_key, use_sudo=True)

        elif step == 18:
            print("==> Making changes to /proc filesystem permanantly")
            text = ["vm.max_map_count = 600000", "kernel.pid_max = 200000"]
            self.append_to_file_on_multiple_instances(self.slave_instances,
                                                      "/etc/sysctl.conf",
                                                      text, use_sudo=True)
            self.run_cmd_on_multiple_instances(self.slave_instances, "sudo sysctl -p", use_sudo=True)

        elif step == 19:
            print ("==> Check that deployment is fine")
            hydra_instance = self.master_instances[0]
            hydra_instance.run_cmd("source ~/venv/bin/activate && cd " + dst_work_dir +
                                   "/hydra-master && pyb run_integration_tests -x run_unit_tests")

            print ("*********************************************************************************************")
            print ("Mesos/Marathon cluster along with Hydra is up and running. \n"
                   "Master nodes IPs : %s \n"
                   "Slave nodes IPs : %s \n"
                   "You can do ssh <instance_username>@%s to run Hydra test \n"
                   % (self.masters_ips_list, self.slaves_ips_list, self.master_instances[0].ip))
            print ("*********************************************************************************************")

    @staticmethod
    def upload_to_multiple_instances(instances, src_pathname, dst_path, use_sudo=False):
        for instance in instances:
            instance.get_file(src_pathname, dst_path, use_sudo)

    @staticmethod
    def run_cmd_on_multiple_instances(instances, cmd, use_sudo=False):
        for instance in instances:
            instance.run_cmd(cmd, use_sudo)

    @staticmethod
    def append_to_file_on_multiple_instances(instances, file_name, text, use_sudo=False):
        for instance in instances:
            instance.append_to_file(file_name, text, use_sudo)

    def get_nodes_ips_list(self, prefix):
        deployment_id = self.config.deployment_id
        common_section = self.config.config_sections[0]
        emailid = common_section.emailid
        compute = common_section.compute

        filt = "name eq " + emailid + "-" + deployment_id + "-" + prefix + ".*"
        results = compute.instances().list(project=common_section.project,
                                           zone=common_section.zone, filter=filt).execute()
        ips = list()
        for instance in results['items']:
            ips.append(instance["networkInterfaces"][0]["networkIP"])
        return ips

    def __create_instances(self, dep_id, common_section, config_sections):
        emailid = common_section.emailid
        instance_user_name = common_section.instance_user_name
        # Launch instances
        for section in config_sections:
            section_name = section.section_name
            count = int(section.count)
            tag = section.tag
            machinetype = section.machinetype
            disk1image = section.disk1image
            disk2image = section.disk2image
            disk1type = section.disk1type
            disk2type = section.disk2type
            disk1size = section.disk1size
            disk2size = section.disk2size

            for num in range(count):
                instance_name = emailid + "-" + dep_id + "-" + section_name + "-" + tag + "-" + str(num)
                disk1 = Disk(instance_name + "-d1", disk1image, disk1size, disk1type)
                disk2 = Disk(instance_name + "-d2", disk2image, disk2size, disk2type)
                disk1.create()
                disk2.create()

                disk_list = [disk1, disk2]
                instance = Instance(instance_name, disk_list, machinetype, instance_user_name)
                instance.create(common_section)
                if section_name == "master":
                    self.master_instances.append(instance)
                else:
                    self.slave_instances.append(instance)
                self.instances.append(instance)

    @staticmethod
    def create_zk_conf_script(conf):
        pathname = "/tmp/zoo.cfg"
        tfile = open(pathname, 'w')
        conf += """
tickTime=2000
initLimit=10
syncLimit=5
dataDir=/var/lib/zookeeper
clientPort=2181
"""
        tfile.write(conf)
        tfile.close()
        return pathname

    @staticmethod
    def create_slave_conf_script(ip):
        (fd, pathname) = mkstemp(prefix="slave_conf_")
        tfile = os.fdopen(fd, "w")
        script = """
    # ZooKeeper will be pulled in and installed as a dependency automatically.
    # The slaves do not require to run their own zookeeper instances
        sudo service zookeeper stop
        sudo bash -c "echo manual | sudo tee /etc/init/zookeeper.override"
    # make sure the Mesos master process doesn't start on our slave servers.
        sudo bash -c "echo manual | sudo tee /etc/init/mesos-master.override"
        sudo service mesos-master stop || true
        echo """ + ip + """ | sudo tee /etc/mesos-slave/ip
        sudo cp /etc/mesos-slave/ip /etc/mesos-slave/hostname
        sudo service mesos-slave stop || true
        sudo service mesos-slave start
    #  sudo apt-get -y install python-dev python-pip
    #  sudo apt-get -y install libzmq3-dev libtool pkg-config build-essential autoconf automake
    #  sudo pip install psutil pyzmq protobuf
    """
        tfile.write(script)
        tfile.close()
        return pathname

    @staticmethod
    def create_hydra_conf(master_node_ip, num_slave_nodes):
        pathname = "/tmp/hydra.ini"
        tfile = open(pathname, 'w')
        # cluster0: slave_id.slave-set1_0
        # cluster1: slave_id.slave-set1_1
        slave_name_str = ""
        for i in range(num_slave_nodes):
            slave_name_str = slave_name_str + 'cluster' + str(i) + ': slave_id.slave-set1_' + str(i) + os.linesep

        string = """[marathon]
ip: """ + master_node_ip + """
port: 8080
app_prefix: g1

[mesos]
ip: """ + master_node_ip + """
port: 5050
""" + slave_name_str + """
[hydra]
port: 9800
dev: eth0
"""
        tfile.write(string)
        tfile.close()
        return pathname

    # This function is purely for debugging purposes.
    def debug(self):
        print ("*** For testing purpose only ***")
        # mas = Instance("mual-master-mas-0", list(), "n1-standard-4", "plumgrid")
        # mas.ip = "10.10.0.23"
        # self.master_instances.append(mas)
        # sla = Instance("mual-slave1-slave-set1-0", list(), "n1-standard-4", "plumgrid")
        # sla.ip = "10.10.0.46"
        # self.slave_instances.append(sla)
        # self.instances = self.master_instances + self.slave_instances
        # self.masters_ips_list = self.get_nodes_ips_list("master")
        # self.slaves_ips_list = self.get_nodes_ips_list("slave")
        # self.all_ips_list = self.masters_ips_list + self.slaves_ips_list

    def cleanup(self):
        common_section = self.config.config_sections[0]
        dep_id = self.config.deployment_id
        emailid = common_section.emailid
        compute = common_section.compute
        project = common_section.project
        zone = common_section.zone

        # Removing master instances.
        filt = "name eq " + emailid + "-" + dep_id + "-master.*"
        results = compute.instances().list(project=project, zone=zone, filter=filt).execute()
        for instance in results['items']:
            name = instance["name"]
            print ("Removing %s ...." % name)
            compute.instances().delete(project=project, zone=zone, instance=name).execute()

        # Removing slave instances.
        filt = "name eq " + emailid + "-" + dep_id + "-slave.*"
        results = compute.instances().list(project=project, zone=zone, filter=filt).execute()
        for instance in results['items']:
            name = instance["name"]
            print ("Removing %s ...." % name)
            compute.instances().delete(project=project, zone=zone, instance=name).execute()
