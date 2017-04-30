#!/usr/bin/env python

"""
zbackup

    Usage:
        zbackup fs create <fs> [<group> <pool>]
        zbackup fs snapshot <fs> [<group> <pool>]
        zbackup run <host> [<group> <pool>]
        zbackup -h | --help
        zbackup --version
"""

import docopt
import sh
import yaml
import sys
from os import path, makedirs
from datetime import datetime
from operator import itemgetter


def create_filesystem(filesystem):
    sh.zfs("create", filesystem)


def snapshot_filesystem(filesystem):
    sh.zfs("snapshot", filesystem)


def delete_snapshots(filesystem, retention=None):
    if retention is None:
        print "Snapshot retention not set"
        sys.exit(8)

    snapshots_raw = sh.zfs('list', '-H', '-r', '-t', 'snap', filesystem).split('\n')

    snapshots = list()
    for snap in snapshots_raw:
        if not snap:
            continue

        f, s = snap.split('\t')[0].split('@')
        snapshots.append((f, datetime.strptime(s, "%d-%m-%Y-%X")))

    sorted_snaps = sorted(snapshots, key=itemgetter(1), reverse=True)

    if len(sorted_snaps) > retention:
        snaps_to_delete = sorted_snaps[retention:]
    else:
        snaps_to_delete = None

    if snaps_to_delete:
        for fs_name, snap_name in snaps_to_delete:
            print "zfs destroy", fs_name + '@' + datetime.strftime(snap_name, "%d-%m-%Y-%X")
            sh.zfs("destroy", fs_name + '@' + datetime.strftime(snap_name, "%d-%m-%Y-%X"))


with open('zbackup.yaml') as config_fd:
    config = yaml.load(config_fd)

if __name__ == '__main__':

    options = docopt.docopt(__doc__)
    defaults = config['default']

    pool_name = options['<pool>'] or defaults.get('pool', None)
    pool = config.get(pool_name)

    if pool is None:
        print "No pool given."
        sys.exit(6)

    if options['fs']:
        group = options['<group>'] or pool.get('group')
        fs = "{poolname}/{group}/{filesystem}".format(poolname=pool_name,
                                                      group=group,
                                                      filesystem=options['<fs>'])

        # zbackup fs create filesystem
        if options['fs'] and options['create']:
            try:
                create_filesystem(fs)
            except sh.ErrorReturnCode_1:
                print "{} already exists".format(fs)

        # zbackup fs snapshot filesystem
        if options['fs'] and options['snapshot']:
            snapname = datetime.now().strftime(group.get('snapname'))
            retention = pool['groups'].get(group).get('retention') or defaults.get('retention')

            delete_snapshots(fs, retention=retention)
            #snapshot_filesystem(fs + '@' + snapname)
