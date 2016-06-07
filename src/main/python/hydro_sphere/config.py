#!/usr/bin/python
import ConfigParser
import os
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


class DeploymentConfigSection(object):
    def __init__(self, section_name, count, tag, machinetype,
                 disk1image, disk2image, disk1type, disk2type, disk1size, disk2size):
        self.section_name = section_name
        self.count = count
        self.tag = tag
        self.machinetype = machinetype
        self.disk1image = disk1image
        self.disk2image = disk2image
        self.disk1type = disk1type
        self.disk2type = disk2type
        self.disk1size = disk1size
        self.disk2size = disk2size


class CommonConfigSection(object):
    def __init__(self, section, emailid, sshkey, instance_user_name, project, zone, network):
        self.section_name = section
        self.emailid = emailid.split("@")[0]
        self.sshkey = sshkey
        self.instance_user_name = instance_user_name
        self.project = project
        self.zone = zone
        self.network = network
        self.credentials = GoogleCredentials.get_application_default()
        self.compute = discovery.build('compute', 'v1', credentials=self.credentials)


class Config(object):
    def __init__(self, deployment_id):
        self.deployment_id = deployment_id
        self.config_sections = list()

    def parse_config_file(self, config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        sections = config.sections()
        for section in sections:
            if section != "common":
                count = config.get(section, "count")
                tag = config.get(section, "tag")
                machinetype = config.get(section, "machinetype")
                disk1image = config.get(section, "disk1image")
                disk2image = config.get(section, "disk2image")
                disk1type = config.get(section, "disk1type")
                disk2type = config.get(section, "disk2type")
                disk1size = config.get(section, "disk1size")
                disk2size = config.get(section, "disk2size")
                deployment_config_section = DeploymentConfigSection(section, count, tag, machinetype, disk1image,
                                                                    disk2image, disk1type, disk2type, disk1size,
                                                                    disk2size)
                self.config_sections.append(deployment_config_section)
            elif section == "common":
                emailid = config.get(section, "emailid")
                sshkey = config.get(section, "sshkey")
                instance_user_name = config.get(section, "instanceusername")
                project = config.get(section, "project")
                zone = config.get(section, "zone")
                network = config.get(section, "network")
                common_config_section = CommonConfigSection(section, emailid, sshkey, instance_user_name, project,
                                                            zone, network)
                # Insert common section at start of the list
                self.config_sections.insert(0, common_config_section)

        return self.config_sections

if __name__ == "__main__":
    deployment_config = Config("mali")
    config_sections = deployment_config.parse_config_file(os.getcwd() + "/bu_setup_config.ini")
    for section in config_sections:
        print ("section_name:%s" % section.section_name)
        if section.section_name == "common":
            print ("%s" % section.emailid)
        else:
            print ("%s" % (section.machine_type))
