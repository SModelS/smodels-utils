#!/usr/bin/env python3

""" simple script to get list of all oom-killed processes """

import glob, subprocess, os, shutil

def main():
    files = glob.glob("walk-*out")
    ooms, oofs = [], []
    for f in files:
        h = open ( f, "rt" )
        lines = h.readlines()
        # [walkingWorker] starting 45 @ /scratch-cbe/users/wolfgan.waltenberger/rundir.lfake4/ with cheatcode 0
        h.close()
        for line in lines:
            if "oom" in line:
                ooms.append ( lines[0] )
                oofs.append ( f )
                break
    submitsh = "submit.sh"
    g=open( submitsh,"wt")
    g.write ( "#!/bin/sh\n\n" )
    for oom,oof in zip(ooms,oofs):
        rundir = oom[ oom.find("waltenberger/")+13:oom.find(" with " )-1 ]
        nr = oom [ oom.find("starting")+9:oom.find(" @ ") ]
        nr = int(nr)
        line = "./slurm.py -R %s -n %d -N %d" % ( rundir, nr, nr+1)
        g.write ( line+"\n" )
        line = "rm -rf /scratch-cbe/users/wolfgan.waltenberger/outputs/%s" % oof 
        g.write ( line+"\n\n" )
    g.close()
    os.chmod ( submitsh, 0o755 )
    shutil.copy ( submitsh, "/users/wolfgan.waltenberger" )

main()
