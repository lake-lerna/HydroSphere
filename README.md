# HydroSphere [![Build Status](https://travis-ci.org/tahir24434/HydroSphere.svg?branch=master)](https://travis-ci.org/tahir24434/HydroSphere)
A project to setup Mesos/Marathon Cluster along with Hydra in automated way

This project helps you setting up mesos-marathon cluster along with [Hydra] (https://github.com/lake-lerna/hydra) on cloud (GCE, AWS, Azure). For now, only
GCE is supported. <br />
To setup a cluster with Hydra, use following commands

1. Do Gcloud configurations <br />
    -> curl https://sdk.cloud.google.com | bash <br />
    -> exec -l $SHELL <br />
    -> gcloud auth login <br />
    -> gcloud config set project \<gcloud project name\> <br />
    -> gcloud config set compute/zone \<zone-name e.g us-central1-f\> <br />
    -> gcloud config set compute/region \<region-name e.g us-central1\> <br />
    -> gcloud config set component_manager/fixed_sdk_version 0.9.81 <br />
    -> gcloud components -q update <br />

2. Clone and Install hydra-deploy <br />
  -> git clone https://github.com/lake-lerna/HydroSphere <br />
  -> pushd HydroSphere <br />
  -> pyb install_dependencies <br />
  -> pyb install <br />
  -> popd <br />

3. Setup Mesos-Marathon Cluster and setup Hydra on master node <br />
  First of all, modify the setup configuration file. A sample file is given in hydra_deploy with name setup_config.ini . <br />
  -> pushd HydroSphere/src/main/python/hydro_sphere <br />
  -> python hydro_sphere.py --config_file setup_config.ini --deployment_id \<unique id for deployment\> <br /> --ssh_key_file \<path to your publick key\> <br />
  
  You can access mesos on masterip:5050 and marathon on masterip:8080

4. Login to master node to run test cases <br />
    List current instances <br />
    -> gcloud compute instances list | grep \<user-name\> <br />
    Please note down the IP of your master node. It would be with name \<emailid-deploymentid-*\> <br />
    -> ssh \<master-ip\> <br />
    -> cd hydra-master <br />
    -> source ../venv/bin/activate <br />
    -> hydra zmq <br />

TO setup only mesos cluster without hydra, you can give following command <br />
-> pushd HydroSphere/src/main/python/hydro_sphere <br />
-> python mesos_marathon_setup.py --config_file setup_config.ini --deployment_id <unique id for deployment> --ssh_key_file \<path to your public key\> <br />

If you want to setup hydra later on Mesos/Maratho cluster, you can issue the command <br />
-> python hydra_setup_script.py --deployment_id \<unique id for deployment\> --instance_user \<instance_user_name mentioned in your config file\>
