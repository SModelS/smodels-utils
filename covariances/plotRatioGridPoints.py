#!/usr/bin/env python3

""" Plot the ratio between the upper limit from the UL map
    versus the efficiency map but only at the grid points"""

import matplotlib.pyplot as plt
import matplotlib
import uproot
from smodels_utils.helper import prettyDescriptions
from smodels.experiment.databaseObj import Database
from smodels.experiment import txnameObj
from smodels.base.physicsUnits import GeV, pb, fb

txnameObj.TxNameData._keep_values = True

def main():
    import argparse
    argparser = argparse.ArgumentParser( description = "plot ratio between upper limit map and efficiency map, at grid points" )
    argparser.add_argument ( "-a", "--analysis",
            help="analysis [ATLAS-SUSY-2018-14]",
            type=str, default="ATLAS-SUSY-2018-14" )
    argparser.add_argument ( "-e", "--efficiencies",
            help="plot efficiencies, not ratios", action="store_true" )
    args = argparser.parse_args()
    db = Database ( "../../smodels-database" )
    for txname in [ "TSelSelDisp", "TSmuSmuDisp" ]:
        erf = db.getExpResults ( analysisIDs = [ args.analysis ], useNonValidated=True,
                                 dataTypes = [ "efficiencyMap" ], txnames = [ txname ] )[0]
        er0 = db.getExpResults ( analysisIDs = [ args.analysis ], useNonValidated=True, 
                                 dataTypes = [ "upperLimit" ], txnames = [ txname ] )[0]
        gridpoints = eval ( er0.datasets[0].txnameList[0].txnameData.origdata )
        x,y,z=[],[],[]
        for point in gridpoints:
            massvec = point[0]
            x.append ( massvec[0][0][0].asNumber(GeV) )
            y.append ( massvec[0][0][1].asNumber(GeV) )
            uls= []
            maxeul, maxoul= 1e9*pb, 1e9*pb
            for ds in erf.datasets[:1]:
                oul = ds.dataInfo.upperLimit
                eul = ds.dataInfo.expectedUpperLimit
                eff = ds.getEfficiencyFor ( txname, massvec )
                uls.append ( { "expected": eul/eff, "observed": oul/eff } )
                if eul/eff < maxeul:
                    maxeul = eul/eff
                    maxoul = oul/eff
            if args.efficiencies:
                z.append ( eff )
            else:
                z.append ( float ( maxoul / point[1] ) )
        plt.scatter ( x, y, c=z, norm = matplotlib.colors.LogNorm()  )
        cb = plt.colorbar()
        if args.efficiencies:
            zlabel = "eff of best SR" 
        else:
            zlabel = "ratio eff / ul"
        cb.set_label ( zlabel )
        
        plt.title ( f"ATLAS-SUSY-2018-14:{txname}" )
        plt.yscale ( "log" )
        plt.xlabel ( "mass(mother) [GeV]" )
        plt.ylabel ( "width(mother) [GeV]" )
        if args.efficiencies:
            fname = f"eff_{txname}.png"
        else:
            fname = f"ratio_{txname}.png"
        plt.savefig ( fname )
        plt.clf()

main()
