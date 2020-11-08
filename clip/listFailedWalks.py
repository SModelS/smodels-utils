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
        idx = 0
        for line in lines:
            if "Lmod has detected the following error" in line:
                idx = 12
                continue ## "ml --latest singularity" error
            if "oom" in line or "rror" in line:
                ooms.append ( lines[idx] )
                oofs.append ( f )
                print ( "[listFailedWalks] in file:", f )
                print ( "[listFailedWalks] line 0", lines[idx] )
                print ( "[listFailedWalks] line", line )
                print ( )
                break
    submitsh = "submit.sh"
    g=open( submitsh,"wt")
    g.write ( "#!/bin/sh\n\n" )
    for oom,oof in zip(ooms,oofs):
        rundir = oom[ oom.find("waltenberger/")+13:oom.find(" with " )-1 ]
        nr = oom [ oom.find("starting")+9:oom.find(" @ ") ]
        try:
            nr = int(nr)
            line = "./slurm.py -R %s -n %d -N %d" % ( rundir, nr, nr+1)
            g.write ( line+"\n" )
            line = "rm -rf /scratch-cbe/users/wolfgan.waltenberger/outputs/%s" % oof 
            g.write ( line+"\n\n" )
        except Exception as e:
            print ( "exception", e, nr )
    g.close()
    os.chmod ( submitsh, 0o755 )
    shutil.copy ( submitsh, "/users/wolfgan.waltenberger" )

main()
