#!/usr/bin/python
from shell_command import shell_call


class Disk(object):
    def __init__(self, name, image, size, type):
        self.name = name
        self.image = image
        self.size = size
        self.type = type

    def create(self):
        if self.image == "ubuntu-12-04" or self.image == "ubuntu-14-04":
            cmd = "gcloud compute disks create " + self.name + " --image " + self.image + " --type " + self.type + \
                  " --size=" + self.size + " -q"
        elif self.image is None:
            cmd = "gcloud compute disks create " + self.name + " --type " + self.type + " --size=" + self.size + " -q"
        else:
            cmd = "gcloud compute disks create " + self.name + " --source-snapshot " + self.image + \
                  " --type " + self.type + " --size=" + self.size + " -q"
        print ("disk_cmd=%s" % cmd)
        shell_call(cmd)
