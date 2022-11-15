#!/usr/bin/env python3

""" clears out old temp files """

import os, time, glob, shutil

def clear():
    files = glob.glob ( "tmp*" )
    t0=time.time()
    for f in files:
        timestamp = ( t0 - os.stat ( f ).st_mtime ) / 60 / 60 / 24.
        if timestamp > 3: ## 3 days
            print ( f, timestamp )
            shutil.rmtree ( f )

if __name__ == "__main__":
    clear()
