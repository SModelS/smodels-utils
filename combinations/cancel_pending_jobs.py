#!/usr/bin/env python3

import subprocess

def main():
    a= subprocess.getoutput ( "slurm q | grep QOSMax" )
    for line in a.split("\n" ):
        jobid = line[:8].strip()
        print ( "LINE >%s<" % jobid )
        subprocess.getoutput ( "scancel %s" % jobid )

main()
