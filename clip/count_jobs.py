#!/usr/bin/env python3

import subprocess

def main():
    a = subprocess.getoutput ( "slurm q | grep PEND | wc -l" )
    print ( "pending", a )
    a = subprocess.getoutput ( "slurm q | grep RUNNING | wc -l" )
    print ( "running", a )

main()
