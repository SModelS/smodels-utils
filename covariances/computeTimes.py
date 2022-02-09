#!/usr/bin/env python3

""" get the average runtimes out of validation files """

import numpy, os
from smodels_utils.helper.various import getPathName

def computeTimes ( validationfile ):
    print ( f"[computeTimes] computing for {validationfile}" )
    f=open(validationfile,"rt")
    txt=f.read()
    f.close()
    exec(txt,globals())
    ts, ts0 = [], []
    for d in validationData[:]:
        if "t" in d:
            t = d["t"]
            ts.append ( t )
            if t > 0.:
                ts0.append ( t )
    print ( f"I have {len(ts)} entries. t={numpy.mean(ts):.2f}+-{numpy.std(ts):.2f} seconds" )
    print ( f"{len(ts)-len(ts0)} entries are zero. without them we have: t={numpy.mean(ts0):.2f}+-{numpy.std(ts0):.2f} seconds" )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser( description= "very simple facility to compute average runtimes from validation files. supply either fullpath, or validationfile, dbpath, and analysis id" )
    ap.add_argument('-f','--fullpath',help="full path to validation file. takes precedence. [None]",
                    default = None, type=str )
    ap.add_argument('-v','--validationfile',help="validation file [TChiWZoff_2EqMassAx_EqMassBy.py]",
                    default = "TChiWZoff_2EqMassAx_EqMassBy.py", type=str )
    ap.add_argument('-a','--analysisid',help="analysis id [CMS-SUS-16-039-agg]",
                    default = "CMS-SUS-16-039-agg", type=str )
    ap.add_argument('-d','--dbpath',help="database path [~/git/smodels-database]",
                    default = "~/git/smodels-database", type=str )
    args = ap.parse_args()
    if args.fullpath != None:
        filename = os.path.expanduser ( args.validationfile )
        computeTimes ( filename )
        sys.exit()
    filename = getPathName ( args.dbpath, args.analysisid, args.validationfile )
    computeTimes ( filename )
