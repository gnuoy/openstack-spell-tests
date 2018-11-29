# Test openstack-lxd conjure up spell

Tests assume they are running on a dedicated piece of hardware as they will
install dep and snap packages and may reinstall lxd. Bionic is the only Ubuntu
release tested atm.

#### Script 01-test-conjure-up.sh

Used to prepare the server and run conjure-up with the openstack-lxd spell. The
script mimics the published manual instructions.

#### Script 02-setup-testing-env.sh

Install pre-requisits for running the post-deployment functional tests.

#### Script 03-run-post-deploy-tests.sh

Runs the post-deployment functional tests. See below for test details.

#### test test-dashboard.py

This test script is called by **03-run-post-deploy-tests.sh** and uses Selenium
to mimic a users interactions with Horizon as per the published manual
instructions.

#### test test-connectivity.py

Ok, you read this far and you got me. I just couldn't face using Selenium to
check that the instance was active and to then add a floating IP. This script
is also called by **03-run-post-deploy-tests.sh**, it checks that the instance
launched by **test-dashboard.py** came up and is active, it then adds a
floating IP and SSHs into the guest.
