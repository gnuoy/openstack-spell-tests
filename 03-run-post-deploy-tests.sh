#!/bin/bash

source ~/test_env

./test-dashboard.py  -u $OS_USERNAME -p $OS_PASSWORD -d $OS_USER_DOMAIN_NAME -j $PHANTOMJS_PATH -v tmbtil2
./test-connectivity.py -v tmbtil2 --key-file $PRIV_KEY_PATH

