#!/bin/bash

TEST_ROOT="/home/ubuntu"
TEST_ENV_FILE="${TEST_ROOT}/test_env"
PHANTOM_JS_EXE="${TEST_ROOT}/node_modules/phantomjs-prebuilt/bin/phantomjs"
MODEL_NAME=$(juju switch | awk 'BEGIN {FS="/"} {print $NF}')

function apt_install {
    sudo apt install --yes virtualenv xvfb npm libfontconfig
}

function fix_create_volume_default {
    juju config openstack-dashboard default-create-volume=False
}

function install_phantomjs {
    if [[ ! -f $PHANTOM_JS_EXE ]]; then
        ( cd $TEST_ROOT; npm install phantomjs-prebuilt; )
    fi
}

function setup_venv {
    virtualenv --python python3 ${TEST_ROOT}/venv3
    source ${TEST_ROOT}/venv3/bin/activate
    pip install selenium PyVirtualDisplay xvfbwrapper
    pip install git+https://github.com/openstack-charmers/zaza.git
}

function grab_ssh_key {
    juju scp nova-cloud-controller/0:/home/ubuntu/.ssh/id_rsa ${TEST_ROOT}/ubuntu_priv_key
    chmod 600 ${TEST_ROOT}/ubuntu_priv_key
}

function grab_novarc {
    juju scp nova-cloud-controller/0:/home/ubuntu/novarc ${TEST_ROOT}/novarc
}

function create_test_env {
    grep export ${TEST_ROOT}/novarc > ${TEST_ENV_FILE}
    echo "export MODEL_NAME=$MODEL_NAME" >> ${TEST_ENV_FILE}
    echo "export DISPLAY=:1" >> ${TEST_ENV_FILE}
    echo "export PRIV_KEY_PATH=${TEST_ROOT}/ubuntu_priv_key" >> ${TEST_ENV_FILE}
    echo "export PHANTOMJS_PATH=$PHANTOM_JS_EXE" >> ${TEST_ENV_FILE}
    echo "source ${TEST_ROOT}/venv3/bin/activate" >> ${TEST_ENV_FILE}
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
