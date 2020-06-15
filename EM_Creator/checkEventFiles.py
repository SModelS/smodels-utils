#!/usr/bin/env python3

import glob, os, time

def main():
    files = glob.glob("mg5results/T*hepmc.gz")
    t0=time.time()
    for f in files:
        mt = os.stat ( f ).st_mtime
        dt = (t0 - mt ) / 60. / 60. ## hours
        if dt < 2.:
            continue
        print ( f, dt )

main()
