#!/usr/bin/env python3

import pickle, os, sys
from randomWalk import Model # RandomWalker
from hiscore import Hiscore
from smodels.tools.physicsUnits import GeV
import IPython
# from pympler.asizeof import asizeof

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore discusser. to check if this looks correct' )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file with hiscores [hiscore.pcl]',
            type=str, default="hiscore.pcl" )
    argparser.add_argument ( '-t', '--topos',
            help='list also topologies', action="store_true" )
    args = argparser.parse_args()
    h = Hiscore ( 0, False, args.picklefile )
    if not 0 in h.trimmed:
        print ( "i need to the hiscore, trimmed" )
        sys.exit()
    model = h.trimmed[0]
    print ( "Model. Z=%.3f" % model.Z )
    print ( "Best combo" )
    for pred in model.bestCombo:
        print ( " `- %s:%s (%s)" % (pred.analysisId(), pred.dataId(), pred.dataType() ) )
        M="None"
        if not pred.mass == None:
            M=""
            for b in pred.mass:
                for m in b:
                    maN = int(m.asNumber(GeV))
                    if str(maN) not in M:
                        M += "%d, " % m.asNumber(GeV)
            if len(M)>2:
                M=M[:-2]
        #print ( "     masses: %s" % ( M ) )
        if args.topos:
            print ( "    txnames: %s" % ( pred.txnames ) )
        tx = pred.txnames[0]
        print ( "       nobs: %s, nbg: %s +/- %s" %  (tx._infoObj.getInfo("observedN" ),
                    tx._infoObj.getInfo("expectedBG"),tx._infoObj.getInfo("bgError") ) )

if __name__ == "__main__":
    main()
