#!/bin/bash

PHANTOM_JS_EXE="/home/ubuntu/node_modules/phantomjs-prebuilt/bin/phantomjs"
MODEL_NAME=$(juju switch | awk 'BEGIN {FS="/"} {print $NF}')

function apt_install {
    sudo apt install --yes virtualenv xvfb npm
}

function fix_create_volume_default {
    juju config openstack-dashboard default-create-volume=False
}

function install_phantomjs {
    if [[ ! -f $PHANTOM_JS_EXE ]]; then
        npm install phantomjs-prebuilt
    fi
}

function setup_venv {
    virtualenv --python python3 venv3
    source venv3/bin/activate
    pip install selenium PyVirtualDisplay xvfbwrapper
    pip install git+https://github.com/openstack-charmers/zaza.git
}

function grab_ssh_key {
    juju scp nova-cloud-controller/0:/home/ubuntu/.ssh/id_rsa ubuntu_priv_key
    chmod 600 ubuntu_priv_key
}

function grab_novarc {
    juju scp nova-cloud-controller/0:/home/ubuntu/novarc novarc
}

function create_test_env {
    grep export novarc > test_env
    echo "export MODEL_NAME=$MODEL_NAME" >> test_env
    echo "export DISPLAY=:1" >> test_env
    echo "export PRIV_KEY_PATH=/home/ubuntu/ubuntu_priv_key" >> test_env
    echo "export PHANTOMJS_PATH=$PHANTOM_JS_EXE" >> test_env
    echo "source venv3/bin/activate" >> test_env
}

apt_install
# Should be a noop when https://github.com/conjure-up/spells/pull/234 gets
# pulled into conjure-up snap
fix_create_volume_default
install_phantomjs
setup_venv
grab_ssh_key
grab_novarc
create_test_env
