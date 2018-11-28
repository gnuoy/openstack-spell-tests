#!/bin/bash

sudo apt install --yes virtualenv xvfb npm
npm install phantomjs-prebuilt
virtualenv --python python3 venv3
source venv3/bin/activate
pip install selenium PyVirtualDisplay xvfbwrapper
pip install git+https://github.com/openstack-charmers/zaza.git

juju scp nova-cloud-controller/0:/home/ubuntu/.ssh/id_rsa ubuntu_priv_key
chmod 600 ubuntu_priv_key
juju scp nova-cloud-controller/0:/home/ubuntu/novarc novarc
grep export novarc > test_env
echo "export MODEL_NAME=$(juju switch | awk 'BEGIN {FS="/"} {print $NF}')" >> test_env
echo "export DISPLAY=:1" >> test_env
echo "export PRIV_KEY_PATH=/home/ubuntu/ubuntu_priv_key" >> test_env
echo "export PHANTOMJS_PATH=/home/ubuntu/node_modules/phantomjs-prebuilt/bin/phantomjs" >> test_env
echo "source venv3/bin/activate" >> test_env
