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
            if "oom" in line or "rror" in line:
                ooms.append ( lines[0] )
                oofs.append ( f )
                print ( "[listFailedWalks] in file:", f )
                print ( f"[listFailedWalks] line 0: >>>{lines[0]}<<<" )
                print ( "[listFailedWalks] line with error:", line )
                print ( )
                break
    submitsh = "submit.sh"
    g=open( submitsh,"wt")
    g.write ( "#!/bin/sh\n\n" )
    for oom,oof in zip(ooms,oofs):
        rundir = oom[ oom.find(f"{os.environ['USER']}/")+13:oom.find(" with " )-1 ]
        nr = oom [ oom.find("starting")+9:oom.find(" @ ") ]
        try:
            nr = int(nr)
            line = "./slurm.py -R %s -n %d -N %d" % ( rundir, nr, nr+1)
            g.write ( line+"\n" )
            line = f"rm -rf /scratch-cbe/users/{os.environ['USER']}/outputs/%s" % oof
            g.write ( line+"\n\n" )
        except Exception as e:
            print ( "exception", e, nr )
    g.close()
    os.chmod ( submitsh, 0o755 )
    shutil.copy ( submitsh, f"{os.environ['HOME']}" )

main()
