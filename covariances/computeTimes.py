#!/usr/bin/env python3

import numpy

def computeTimes ( validationfile ):
    f=open(validationfile,"rt")
    txt=f.read()
    f.close()
    exec(txt,globals())
    ts, ts0 = [], []
    for d in validationData[:3]:
        if "t" in d:
            t = d["t"]
            ts.append ( t )
            if t > 0.:
                ts0.append ( t )
    nts = numpy.array(ts)
    print ( f"I have {len(ts)} entries. t={numpy.mean(ts):.2f}+-{numpy.std(ts):.2f} seconds" )
    print ( f"{len(nts[nts==0.])} entries are zero. without them we have: t={numpy.mean(ts0):.2f}+-{numpy.std(ts0):.2f} seconds" )

if __name__ == "__main__":
    computeTimes ( "/home/walten/git/smodels-database/13TeV/CMS/CMS-SUS-16-048-agg/validation/TChiWZoff_2EqMassAx_EqMassBy.py" )
