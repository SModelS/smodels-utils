#!/usr/bin/env python3

""" check running jobs, write a submission file with missing """

import subprocess, re, os, shutil

def resubmit ( keyw ):
    """ check for keyword """
    out = subprocess.getoutput ( "slurm q | grep %s" % keyw )
    lines = out.split ("\n" )
    nrs = set()
    for line in lines:
        tokens = re.split("\s+", line)
        nr = tokens[2].replace("RUN","")
        nr = nr.replace(keyw,"")
        if "." in nr:
            nr = nr[:nr.find(".")]
        nr = int(nr)
        nrs.add ( nr )
    missing = set()
    for i in range(50):
        if not i in nrs:
            missing.add ( i )
    print ( missing )
    f=open("submit.sh","wt")
    f.write ( "#!/bin/sh\n" )
    for i in missing:
        f.write ( "./slurm.py -R rundir.history -n %d -N %d\n" % ( i, i+1 ) )
    f.close()
    os.chmod( "submit.sh", 0o755 ) # 1877 is 0o755

resubmit ( "history_" )
