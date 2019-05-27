#!/usr/bin/env python3

import pickle, os, sys
from randomWalk import Model # RandomWalker
sys.path.insert(0,"../" )
from smodels_utils.plotting import rulerPlotter, decayPlotter

def obtain ( number ):
    """ obtain hiscore number <number> """
    f=open("hiscore.pcl","rb" )
    hiscores = pickle.load ( f )
    f.close()
    keys = list ( hiscores.keys() )
    keys.sort( reverse=True )
    Z = keys[number]
    print ( "obtaining #%d: Z=%.2f" % (number, Z ) )
    return hiscores[ Z ]

def plot ( number ):
    ## plot hiscore number "number"
    model = obtain ( number )
    print ( "[plot] create slha file" )
    model.createSLHAFile ( "plot.slha" )
    print ( "[plot] now draw ruler" )
    rulerPlotter.draw ( "./plot.slha", "ruler.png" )
    print ( "[plot] done with the ruler" )
    options = { "tex": True, "color": True, "dot": True }
    ## FIXME add cross sections.
    # decayPlotter.draw ( "./plot.slha", "decays.png", options )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore model plotter')
    argparser.add_argument ( '-n', '--number',
            help='which hiscore to plot [0]',
            type=int, default=0 )
    args = argparser.parse_args()
    plot ( args.number ) 
