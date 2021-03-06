#!/bin/bash

spell_branch=$1

function do_lxd_snap_install {
     sudo snap install lxd
     sudo addgroup lxd || true
     sudo usermod -a -G lxd $(id -n -u)
}

function do_lxd_snap_migrate {
     sudo lxd.migrate -yes
}

function do_lxd_init {
    echo "Running lxd preseed init"
    cat <<EOF | lxd init --preseed
config: {}
networks:
- config:
    ipv4.address: 10.8.8.1/24
    ipv4.nat: "true"
    ipv6.address: none
  description: ""
  managed: false
  name: lxdbr0
  type: ""
storage_pools:
- config:
    size: 40GB
  description: ""
  name: default
  driver: zfs
profiles:
- config: {}
  description: ""
  devices:
    eth0:
      name: eth0
      nictype: bridged
      parent: lxdbr0
      type: nic
    root:
      path: /
      pool: default
      type: disk
  name: default
cluster: null
EOF
}

function do_conjure_up_install {
    sudo snap install conjure-up --classic
}

function write_conjure_file {
cat <<EOF> "$1"
spell: openstack-novalxd
cloud: localhost
color: false
no-report: true
no-track: true
debug: true
EOF
}
function run_conjure_up {
    if [[ -n $2 ]]; then
        sg lxd "/snap/bin/conjure-up -c $1 --spells-dir=$2"
    else
        sg lxd "/snap/bin/conjure-up -c $1"
    fi
}
case $(which lxd) in 
    "/usr/bin/lxd")
        echo "Replacing LXD from pkg with snap"
        do_lxd_snap_install
        do_lxd_snap_migrate
        ;;
    "/snap/bin/lxd")
        echo "LXD from snap found"
        ;;
    "")
        echo "Installing LXD from snap"
        do_lxd_snap_install
        ;;
esac
if [[ -n $spell_branch ]]; then
    ( cd $HOME; git clone $spell_branch; )
    spell_dir="$HOME/spells"
fi
do_lxd_init
which conjure-up || do_conjure_up_install
conjure_file=$(mktemp)
echo $conjure_file
write_conjure_file $conjure_file
run_conjure_up $conjure_file $spell_dir
