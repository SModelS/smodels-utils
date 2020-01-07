#!/usr/bin/env python3

import pickle, os, sys
sys.path.insert(0,"./")
from csetup import setup
from combiner import Combiner
from plotHiscore import obtain

def getLikelihoods ( bestcombo ):
    """ return dictionary with the likelihoods per analysis """
    llhds= {}
    for tp in bestcombo:
        llhds[ tp.analysisId() ] = tp.getLikelihood ( 1. ) 
    return llhds

def plotLikelihoodFor ( protomodel, pid1, pid2 ):
    """ plot the likelihoods as a function of pid1 and pid2 """
    import numpy
    c = Combiner()
    anaIds = c.getAnaIdsWithPids ( protomodel.bestCombo, [ pid1, pid2 ] )
    ## mass range for pid1
    mpid1 = protomodel.masses[pid1]
    mpid2 = protomodel.masses[pid2]
    fmin,fmax,df=.8,1.2,.1
    fmin,fmax,df=.9,1.01,.1
    rpid1 = numpy.arange ( fmin*mpid1, fmax*mpid1, df*mpid1 )
    rpid2 = numpy.arange ( fmin*mpid2, fmax*mpid2, df*mpid2 )
    masspoints = []
    print ( "range for pid1", pid1, rpid1 )
    print ( "range for pid2", pid2, rpid2 )
    for m1 in rpid1:
        protomodel.masses[pid1]=m1
        for m2 in rpid2:
            protomodel.masses[pid2]=m2
            protomodel.predict( nevents = 100 )
            llhds = getLikelihoods ( protomodel.bestCombo )
            print ( "m1,m2,llhds", m1, m2, llhds )
            masspoints.append ( (m1,m2,llhds) )
    print ( "mass points", masspoints )
    import pickle
    f=open("masspoints.pcl","wb" )
    pickle.dump ( masspoints, f )
    f.close()

def plotTopologyLikelihoods ( protomodel ):
    """ plot the likelihoods of the topologies """
    print ( "[plotHiscore] plotting per topology likelihoods" )
    c = Combiner()
    pids = c.getAllPidsOfCombo ( protomodel.bestCombo )
    print ( "all pids", pids )
    plotLikelihoodFor ( protomodel, 1000021, 1000022 )

def main ():
    rundir = setup()
    import argparse
    argparser = argparse.ArgumentParser(
            description='perform likelhood scans')
    argparser.add_argument ( '-n', '--number',
            help='which hiscore to plot [0]',
            type=int, default=0 )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file to draw from [%s/hiscore.pcl]' % rundir,
            type=str, default="%s/hiscore.pcl" % rundir )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug, info, warn, err [info]',
            type=str, default="info" )
    args = argparser.parse_args()
    if args.picklefile == "default":
        args.picklefile = "%s/hiscore.pcl" % rundir
    protomodel, trimmed = obtain ( args.number, args.picklefile )
    plotTopologyLikelihoods ( protomodel )

if __name__ == "__main__":
    main()
