#!/usr/bin/env python3

""" rudimentary script that copies only new analyses from source to dest """

import glob, subprocess, os, sys

source = "%s/git/smodels/smodels-database" % os.environ["HOME"]
dest = "%s/git/smodels-database" % os.environ["HOME"]

Dirs = glob.glob ( "%s/*/*/*" % source )

for d in Dirs:
    dnew = d.replace ( source, dest )
    if os.path.exists ( dnew ):
        print ( "%s exists already" % dnew )
    else:
        print ( "%s is new" % dnew )
        sys.exit()
