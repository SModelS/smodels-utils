#!/usr/bin/env python3

""" cancel a job, possibly also remove the output files """

import subprocess, os
from typing import Dict

def getTempDirs() -> Dict:
    import subprocess
    o = subprocess.getoutput ( "slurm q | grep _V" )
    lines = o.split("\n")
    D={}
    for line in lines:
        if len(line)==0:
            continue
        tokens = line.split()
        jobid = int(tokens[0])
        tmpf = tokens[2][:-3]
        D[jobid]=tmpf
    return D

    
def cancel ( jobid : int, remove_files : bool = True ):
    """ cancel job <jobid> """
    if jobid == None:
        print ( "please supply a jobid" )
        return
    cmd = f"scancel {jobid}"
    print ( cmd )
    o = subprocess.getoutput ( cmd )
    if not remove_files:
        print ( "not asked to remove temp files." )
        return
    D = getTempDirs()
    if not jobid in D:
        print ( f"could not find {jobid} in list of running jobs" )
        return
    tempfile = D[jobid]
    cmd = f"rm -r {tempfile}"
    print ( cmd )
    o = subprocess.getoutput ( cmd )
    cmd = f"rm {os.environ['OUTPUTS']}/{tempfile}.out".replace("//","/")
    print ( cmd )
    o = subprocess.getoutput ( cmd )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="cancel hpc job" )
    ap.add_argument('-j', '--jobid',
            help='id of job (6 digit number)',
            default = None, type = int)
    ap.add_argument('-r', '--remove_files', action="store_true",
            help='remove all output files as well')
    args = ap.parse_args()
    cancel ( args.jobid, args.remove_files )
