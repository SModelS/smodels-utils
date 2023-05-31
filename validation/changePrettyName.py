#!/usr/bin/env python3

__all__ = [ "change" ]

import os, sys, glob
from os import PathLike
from smodels_utils.helper.various import getSqrts, getCollaboration


def change ( anaid : str, prettyName : str, dbpath = PathLike ):
    """ change all prettynames for anaid, in dbpath """
    c = getCollaboration ( anaid )
    s = getSqrts ( anaid )
    fullpath = os.path.expanduser ( f"{dbpath}/{s}TeV/{c}" )
    files = glob.glob ( f"{fullpath}/{anaid}*/convert.py" )
    files += glob.glob ( f"{fullpath}/{anaid}*/globalInfo.txt" )
    for f in files:
        changeInFile ( prettyName, f )

def changeInFile ( prettyName : str, filename : PathLike ):
    """ change the pretty name in a single file """
    if not os.path.exists ( filename ):
        print ( f"[changePrettyName] file {filename} does not exist" )
        return
    isGlobalInfo = False # true if convert.py, false if globalInfo.txt
    if "globalInfo.txt" in filename:
        isGlobalInfo = True
    f = open ( filename )
    lines = f.readlines()
    f.close()
    hasPrettyName = False
    for line in lines:
        if "prettyName" in line:
            hasPrettyName = True
            break
    if not hasPrettyName:
        print ( f"[changePrettyName] no prettyName defined in {filename}" )
        return
    g = open ( filename, "wt" )
    print ( f"[changePrettyName] changing {filename}" )
    for line in lines:
        if not "prettyName" in line:
            g.write ( line )
            continue
        p1 = line.find ( "=" )
        if isGlobalInfo:
            p1 = line.find(":" )
        if p1 < 1:
            print ( f"[changePrettyName] cannot find separator in {filename}" )
            return
        newline = f"{line[:p1+1]} '{prettyName}'"
        if isGlobalInfo:
            newline = f"{line[:p1+1]} {prettyName}"
        g.write ( newline+"\n" )
    g.close()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Systematically change the pretty name of an analysis in a text database" )
    ap.add_argument('-a', '--analysis', type=str,
            help='analysis id, e.g CMS-SUS-19-006', default=None )
    ap.add_argument('-p', '--prettyName', type=str,
            help='the new pretty name', default=None )
    ap.add_argument('-d', '--dbpath', type=str,
            help='path to the database [~/git/smodels-database]', 
            default="~/git/smodels-database" )
    args = ap.parse_args()
    if args.analysis == None:
        print ( "[changePrettyName] need to specify an analysis" )
        sys.exit()
    if args.prettyName == None:
        print ( "[changePrettyName] need to specify a prettyName" )
        sys.exit()
    change ( args.analysis, args.prettyName, args.dbpath )
