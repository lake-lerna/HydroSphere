# hydra-deploy

This project helps you setting up mesos-marathon cluster along with Hydra on cloud (GCE, AWS, Azure). For now, only
GCE is supported. To setup a cluster with Hydra, use following commands

1. Do Gcloud configurations
    -> curl https://sdk.cloud.google.com | bash <br />
    -> exec -l $SHELL <br />
    -> gcloud auth login <br />

    -> gcloud config set project <gcloud project name> <br />
    -> gcloud config set compute/zone <zone-name e.g us-central1-f> <br />
    -> gcloud config set compute/region <region-name e.g us-central1> <br />
    -> gcloud config set component_manager/fixed_sdk_version 0.9.81 <br />
    -> gcloud components -q update <br />

2. Clone and Install hydra-deploy 
  -> git clone https://github.com/lake-lerna/hydra-deploy
  -> pushd hydra-deploy
  -> pyb install_dependencies
  -> pyb install
  -> popd

3. Setup Mesos-Marathon Cluster and setup Hydra on master node
  First of all, modify the setup configuration file. A sample file is given in hydra_deploy with name setup_config.ini .
  -> pushd hydra-deploy/src/main/python/hydra_deploy
  -> python master_mm_hydra_setup.py --config_file setup_config.ini --deployment_id <unique id for deployment> --ssh_key_file <path to your publick key>
  
  You can access mesos on masterip:5050 and marathon on masterip:8080

4. Login to master node to run test cases
    List current instances
    -> gcloud compute instances list | grep <user-name>
    Please note down the IP of your master node. It would be with name <emailid-deploymentid-*>
    -> ssh <master-ip> 
    -> cd hydra-master
    -> source ../venv/bin/activate
    -> hydra zmq

TO setup only mesos cluster without hydra, you can give following command
-> pushd hydra-deploy/src/main/python/hydra_deploy
  python mesos_marathon_setup.py --config_file setup_config.ini --deployment_id <unique id for deployment> --ssh_key_file <path to your publick key>
