#!/bin/bash

unit_name=${1:-'ubuntu/0'}

if [[ -n $NPM_PROXY ]]; then
    npm_proxy_settings="NPM_PROXY=\"$NPM_PROXY\""
else
    npm_proxy_settings=""
fi

[[ -d venv3 ]] || virtualenv --python python3 venv3  

source venv3/bin/activate
pip install juju-wait
juju-wait

juju ssh $unit_name "source /etc/profile.d/apps-bin-path.sh; git clone https://github.com/gnuoy/openstack-spell-tests.git; cd openstack-spell-tests; ./01-test-conjure-up.sh " && \
juju ssh $unit_name  "source /etc/profile.d/apps-bin-path.sh; cd openstack-spell-tests; $npm_proxy_settings ./02-setup-testing-env.sh && ./03-run-post-deploy-tests.sh"; 

