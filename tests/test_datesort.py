#!/usr/bin/env python

from datetime import datetime



snapshots = [
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Sun Apr 30 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Sun Apr 30 08:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Sat Apr 29 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Fri Apr 28 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Thu Apr 27 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Wed Apr 26 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Tue Apr 25 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Mon Apr 24 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Sun Apr 23 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Sat Apr 22 10:15 2017'],
    [u'backup/hosts/testing01.brownbag@30-04-2017-17:15:22', u'Fri Apr 21 10:15 2017'],
]

rotate = 6


def rotate_snapshots(fs):
    for sname, screation in snapshots:
        ctime = datetime.strptime(screation, "%a %b %d %H:%M %Y")
        delta = datetime.now() - ctime
        if delta.days > rotate:
            print delta, sname

rotate_snapshots('e')
