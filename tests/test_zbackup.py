#!/usr/bin/env python

"""
zbackup

    Usage:
        zbackup fs create <fs> [<group> <pool>] [--configfile=<configfile>]
        zbackup fs destroy <fs> [<group> <pool>] [--configfile=<configfile>]
        zbackup fs snapshot <fs> [<group> <pool>] [--configfile=<configfile>]
        zbackup run <fs> [<group> <pool>] [--configfile=<configfile>]
        zbackup -h | --help
        zbackup --version
    Options:
        --configfile=<configfile>       [default: /etc/zbackup/config.yaml]
"""

import docopt
import sh
import yaml
import sys
from os import path, makedirs
from datetime import datetime
from operator import itemgetter
import re


def write_meta(metadir):
    try:
        makedirs(metadir)
    except OSError:
        pass

    with open(path.join(metadir, 'exclude'), 'wb') as exclude:
        exclude.writelines('\n'.join(group.get('exclude')))

    with open(path.join(metadir, 'include'), 'wb') as include:
        include.writelines('\n'.join(group.get('include', '')))

    with open(path.join(metadir, 'user'), 'wb') as include:
        include.writelines(group.get('rsync_user'))

    with open(path.join(metadir, 'key'), 'wb') as include:
        include.writelines(group.get('rsync_key'))


def merge_plan(backup_plans):
    for plan_name, plan_conf in backup_plans.iteritems():
        if not re.match(plan_conf['match'], options['<fs>']):
            continue

        with open('../' + plan_conf['config']) as plan_fd:
            group.update(yaml.load(plan_fd))


def create_filesystem(filesystem):
    sh.zfs("create", filesystem)
    write_meta('/' + filesystem + '/.meta')


def destroy_filesystem(filesystem):
    sh.zfs("destroy", "-r", filesystem)


def snapshot_filesystem(filesystem):
    sh.zfs("snapshot", filesystem)


def delete_snapshots(filesystem, retention=None, datefmt=None):
    if retention is None:
        print "Snapshot retention not set"
        sys.exit(8)

    # snapshots_raw = sh.zfs('list', '-H', '-r', '-t', 'snap', filesystem).split('\n')

    snapshots = list()
    for snap in snapshots_raw:
        f, s = snap.split('@')
        snapshots.append((f, datetime.strptime(s, datefmt)))

    sorted_snaps = sorted(snapshots, key=itemgetter(1), reverse=True)

    if len(sorted_snaps) > retention:
        snaps_to_delete = sorted_snaps[retention:]
    else:
        snaps_to_delete = None

    if snaps_to_delete:
        for fs_name, snap_name in snaps_to_delete:
            print "zfs destroy", fs_name + '@' + datetime.strftime(snap_name, datefmt)
            # sh.zfs("destroy", fs_name + '@' + snap_name)


def rsync(source, destination, *args):
    rsync_user = group.get('rsync_user')
    rsync_key = "-e 'ssh -i {}'".format(group.get('rsync_key'))
    rsync_args = ['--' + arg for arg in group.get('rsync_args')]
    rsync_include = '--include-from=' + path.join(destination, '.meta', 'include')
    rsync_exclude = '--exclude-from=' + path.join(destination, '.meta', 'exclude')

    print "rsync {key} {args} {exclude} {include} {user}@{src} {dst}".format(key=rsync_key,
                                                                                args=' '.join(rsync_args),
                                                                         user=rsync_user,
                                                                         src=source,
                                                                         dst=destination,
                                                                         exclude=rsync_exclude,
                                                                         include=rsync_include)
    #sh.rsync(*args)


snapshots_raw = [
    'backup/hosts/testing@29-04-2017-20:37:39',
    'backup/hosts/testing@29-04-2017-20:17:39',
    'backup/hosts/testing@28-04-2017-20:37:39',
    'backup/hosts/testing@28-04-2017-10:37:39',
    'backup/hosts/testing@27-04-2016-20:37:39',
    'backup/hosts/testing@26-04-2017-20:37:39',
    'backup/hosts/testing@25-04-2017-20:37:39',
    'backup/hosts/testing@24-04-2017-20:37:39',
]


if __name__ == '__main__':

    options = docopt.docopt(__doc__)
    configfile = options['--configfile']
    with open(configfile) as config_fd:
        config = yaml.load(config_fd)

    defaults = config['default']

    pool_name = options['<pool>'] or defaults.get('pool', None)
    pool = config.get(pool_name)

    group_name = options['<group>'] or pool.get('group')
    group = defaults.copy()

    mountpoint = path.join('/', pool_name, group_name, options['<fs>'])

    # check if plans are defined
    plans = pool['groups'].get(group_name).get('plans', None)

    # update config dict if plans are defined
    if plans:
        merge_plan(plans)
    else:
        group.update(pool['groups'].get(group_name))

    meta_dir = path.join(mountpoint, '.meta')
    if path.exists(meta_dir):
        write_meta(meta_dir)

    if pool is None:
        print "No pool given."
        sys.exit(6)

    if options['run']:
        rsync_from = options['<fs>'] + group.get('rsync_path')
        rsync_to = mountpoint
        rsync(rsync_from, rsync_to)

    if options['fs']:
        fs = "{poolname}/{group}/{filesystem}".format(poolname=pool_name,
                                                      group=group_name,
                                                      filesystem=options['<fs>'])

        # zbackup fs create filesystem
        if options['fs'] and options['create']:
            try:
                create_filesystem(fs)
            except sh.ErrorReturnCode_1:
                print "Filesystem {} already exists".format(fs)

        # zbackup fs create filesystem
        if options['fs'] and options['destroy']:
            try:
                destroy_filesystem(fs)
            except sh.ErrorReturnCode_1:
                print "Filesystem {} does not exist.".format(fs)

        # zbackup fs snapshot filesystem
        if options['fs'] and options['snapshot']:
            retention = group.get('retention')
            delete_snapshots(fs, retention=retention, datefmt=group.get('snapname'))

            snapname = datetime.now().strftime(group.get('snapname'))
            #snapshot_filesystem(fs + '@' + snapname)
