#!/usr/bin/env python3

import subprocess

def main():
    a= subprocess.getoutput ( "slurm q | grep QOSMax" )
    print ( "cancelling", end=" " )
    for line in a.split("\n" ):
        jobid = line[:8].strip()
        print ( "%s" % jobid, end=" " )
        subprocess.getoutput ( "scancel %s" % jobid )
    print ( "." )

main()
