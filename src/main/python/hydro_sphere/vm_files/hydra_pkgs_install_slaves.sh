#!/usr/bin/env bash

sudo apt-get install -y python-dev python-pip libtool pkg-config build-essential autoconf automake

echo "==> Install zeromq"
wget https://github.com/zeromq/zeromq4-1/releases/download/v4.1.4/zeromq-4.1.4.tar.gz
tar xvf zeromq-4.1.4.tar.gz
pushd zeromq-4.1.4
./configure --without-libsodium --prefix=/usr
make -j 4
sudo make install
popd
popd

sudo pip install psutil pyzmq protobuf pika