#!/bin/bash

source ~/test_env

./test-dashboard.py  -u $OS_USERNAME -p $OS_PASSWORD -d $OS_USER_DOMAIN_NAME \
    -j $PHANTOMJS_PATH -f m1.tiny -i bionic-lxd -n internal -v seleniumtest
./test-connectivity.py -v seleniumtest --key-file $PRIV_KEY_PATH

