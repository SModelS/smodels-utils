#!/usr/bin/env python3

import glob, subprocess

def main():
    files = glob.glob("T*jet*/Events/run_01/tag_1_pythia8_events.hepmc.gz" )
    for f in files:
        cmd = "cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/EM_Creator; touch %s" % f
        print ( f )
        o = subprocess.getoutput ( cmd )
        print ( o )

main()
