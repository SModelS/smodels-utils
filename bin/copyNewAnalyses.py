#!/usr/bin/env python3

""" rudimentary script that copies only new analyses from source to dest """

import glob, subprocess, os, sys

source = f"{os.environ['HOME']}/git/smodels/smodels-database"
dest = f"{os.environ['HOME']}/git/smodels-database"

Dirs = glob.glob ( f"{source}/*/*/*" )

for d in Dirs:
    dnew = d.replace ( source, dest )
    if os.path.exists ( dnew ):
        print ( f"{dnew} exists already" )
    else:
        print ( f"{dnew} is new" )
        sys.exit()
