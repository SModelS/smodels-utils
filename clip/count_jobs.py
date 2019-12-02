#!/usr/bin/env python3

import subprocess

def main():
    pend = subprocess.getoutput ( "slurm q | grep PEND | wc -l" )
    print ( "pending", pend )
    running = subprocess.getoutput ( "slurm q | grep RUNNING | wc -l" )
    print ( "running", running )
    remaining = subprocess.getoutput ( "slurm q | grep -v PEND | grep -v RUNNING | grep -v NODELIST | wc -l" )
    if int(remaining)>0:
        print ( "remaining", remaining )

main()
