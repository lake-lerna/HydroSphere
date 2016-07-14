#!/bin/bash
set -e
dst_work_dir=$1

echo "**** $dst_work_dir"
# Pre Script
echo "==> Run pre script"
wget https://raw.githubusercontent.com/zeromq/cppzmq/master/zmq.hpp
#mv zmq.hpp ${dst_work_dir}/hydra-master/src/main/c/zmq
sudo mv zmq.hpp /usr/include/zmq.hpp
sudo apt-get -y install python-dev python-pip rabbitmq-server

echo "==> Install RMQ pre-reqs for unit test using mock backend"
sudo rabbitmqctl add_user hydra hydra
sudo rabbitmqctl set_user_tags hydra administrator
sudo rabbitmqctl set_permissions hydra ".*" ".*" ".*"

echo "==> Setup virtual environemnt"
# Setup virtual environment
sudo pip install virtualenv
venv_dir="/home/$USER/venv"
mkdir ${venv_dir}
virtualenv ${venv_dir}
source ${venv_dir}/bin/activate

echo "==> Install protobuf-c-compiler protobuf-compiler libprotobuf-dev"
sudo apt-get -y install protobuf-c-compiler protobuf-compiler libprotobuf-dev

echo "==> Install zeromq"
pushd ${dst_work_dir}
wget https://github.com/zeromq/zeromq4-1/releases/download/v4.1.4/zeromq-4.1.4.tar.gz
tar xvf zeromq-4.1.4.tar.gz
pushd zeromq-4.1.4
./configure --without-libsodium --prefix=/usr
make -j 4
sudo make install
popd
popd

echo "==> Install Hydra"
pip install pybuilder
pushd ${dst_work_dir}/hydra-master
pyb install_dependencies
pip uninstall -y marathon && pip install -e git+https://github.com/thefactory/marathon-python.git#egg=marathon
pyb analyze

echo "Run script"
pyb publish -x run_unit_tests -x run_integration_tests -x verify
pyb install -x run_unit_tests -x run_integration_tests -x verify


pyb test --verbose
popd
