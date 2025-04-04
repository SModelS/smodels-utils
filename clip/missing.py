#!/usr/bin/env python3

import subprocess, argparse
import cliphelpers

def missing ( pattern ):
    cmd = f"slurm q | grep {pattern}"
    o = subprocess.getoutput ( cmd )
    lines = o.split("\n" )
    found = set()
    for line in lines:
        tokens = line.split()
        if len(tokens)<2:
            continue
        token = tokens[2].replace(".sh","").replace("RUN","").replace(pattern,"")
        token = token.replace(".s","").replace(".","")
        p_ = token.find("_")
        pre = token
        if p_ > -1:
            token=token[p_+1:]
        # print ( "token", token, pre )
        found.add ( int ( token ) )
    # found.sort()
    print ( "found", cliphelpers.describeSet( found ) )
    lost = []
    for i in range(50):
        if not i in found:
            lost.append ( i )
    print ( "lost", cliphelpers.describeSet ( lost ) )

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="list missing walkers")
    argparser.add_argument ( '-p', '--pattern', help='grep for pattern [real]',
                             type=str, default="real" )
    args=argparser.parse_args()
    missing ( args.pattern )
