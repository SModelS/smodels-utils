#!/usr/bin/env python3

""" get the average runtimes out of validation files """

import numpy, os

def computeTimes ( validationfile ):
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
    ap = argparse.ArgumentParser( description= "very simple facility to compute average runtimes from validation files" )
    ap.add_argument('-f','--validationfile',help="path to validation file [~/git/smodels-database/13TeV/CMS/CMS-SUS-16-048-agg/validation/TChiWZoff_2EqMassAx_EqMassBy.py]",
                    default = "~/git/smodels-database/13TeV/CMS/CMS-SUS-16-048-agg/validation/TChiWZoff_2EqMassAx_EqMassBy.py", type=str )
    args = ap.parse_args()
    filename = os.path.expanduser ( args.validationfile )
    print ( f"[computeTimes] computing for {filename}" )
    computeTimes ( filename )
