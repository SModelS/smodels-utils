#!/usr/bin/env python3

import pickle, os, sys
from randomWalk import Model # RandomWalker
sys.path.insert(0,"../" )
from smodels_utils.plotting import rulerPlotter, decayPlotter

def obtain ( number, picklefile ):
    """ obtain hiscore number <number> """
    f=open( picklefile,"rb" )
    hiscores = pickle.load ( f )
    f.close()
    keys = list ( hiscores.keys() )
    keys.sort( reverse=True )
    Z = keys[number]
    print ( "[plotHiscore] obtaining #%d: Z=%.2f" % (number, Z ) )
    return hiscores[ Z ]
    
def discussPredictions ( model ):
    print ( "How the Z comes about. Best combo:" )
    combo = model.bestCombo
    for pred in combo:
        print ( "theory pred: %s:%s" % ( pred.expResult.globalInfo.id, ",".join ( map ( str, pred.txnames ) ) ) )
        # print ( "     `- ", pred.expResult.globalInfo.id, "ana", pred.analysis, "masses", pred.mass, "txnames", pred.txnames, "type", pred.dataType() )


def plot ( number, verbosity, picklefile ):
    ## plot hiscore number "number"
    model = obtain ( number, picklefile )
    print ( "[plotHiscore] create slha file" )
    model.createSLHAFile ( "plot.slha" )
    print ( "[plotHiscore] now draw ruler.png" )
    # rulerPlotter.draw ( "./plot.slha", "ruler.png" )
    print ( "[plotHiscore] now draw decays.png" )
    options = { "tex": True, "color": True, "dot": True }
    ## FIXME add cross sections.
    # decayPlotter.draw ( "./plot.slha", "decays.png", options )
    discussPredictions ( model )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore model plotter')
    argparser.add_argument ( '-n', '--number',
            help='which hiscore to plot [0]',
            type=int, default=0 )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file to draw from [hiscore.pcl]',
            type=str, default="hiscore.pcl" )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug, info, warn, err [info]',
            type=str, default="info" )
    args = argparser.parse_args()
    plot ( args.number, args.verbosity, args.picklefile ) 
