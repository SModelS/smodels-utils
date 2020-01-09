#!/usr/bin/env python3

""" script used to produce the likelihood scans """

import pickle, os, sys, multiprocessing
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

def plotLikelihoodFor ( protomodel, pid1, pid2, 
                        fmin, fmax, df, nevents ):
    """ plot the likelihoods as a function of pid1 and pid2 """
    if pid2 != protomodel.LSP:
        print ("[llhdscans] we currently assume pid2 to be the LSP, but it is %d" % pid2 )
    import numpy
    c = Combiner()
    anaIds = c.getAnaIdsWithPids ( protomodel.bestCombo, [ pid1, pid2 ] )
    ## mass range for pid1
    mpid1 = protomodel.masses[pid1]
    mpid2 = protomodel.masses[pid2]
    print ( "f",fmin,fmax,df )
    rpid1 = numpy.arange ( fmin*mpid1, fmax*mpid1, df*mpid1 )
    rpid2 = numpy.arange ( fmin*mpid2, fmax*mpid2, df*mpid2 )
    masspoints = []
    print ( "range for pid1", pid1, rpid1 )
    print ( "range for pid2", pid2, rpid2 )
    protomodel.createNewSLHAFileName ( prefix="llhd" )
    for m1 in rpid1:
        protomodel.masses[pid1]=m1
        if hasattr ( protomodel, "stored_xsecs" ):
            del protomodel.stored_xsecs ## make sure we compute
        for i2,m2 in enumerate(rpid2):
            if m2 > m1: ## we assume pid2 to be the daughter
                continue
            protomodel.masses[pid2]=m2
            protomodel.predict( nevents = nevents, recycle_xsecs = True )
            llhds = getLikelihoods ( protomodel.bestCombo )
            print ( "m1,m2,llhds", m1, m2, llhds )
            masspoints.append ( (m1,m2,llhds) )
    print ( "mass points", masspoints )
    import pickle
    f=open("mp%d%d.pcl" % ( pid1, pid2 ) ,"wb" )
    pickle.dump ( masspoints, f )
    pickle.dump ( mpid1, f )
    pickle.dump ( mpid2, f )
    f.close()

def main ():
    rundir = setup()
    import argparse
    argparser = argparse.ArgumentParser(
            description='perform likelhood scans')
    argparser.add_argument ( '-n', '--number',
            help='which hiscore to plot [0]',
            type=int, default=0 )
    argparser.add_argument ( '-1', '--pid1',
            help='pid1 [1000021]',
            type=int, default=1000021 )
    argparser.add_argument ( '-2', '--pid2',
            help='pid2 [1000022]',
            type=int, default=1000022 )
    argparser.add_argument ( '-f', '--fmin',
            help='minimum factor to scan [.6]',
            type=float, default=.6 )
    argparser.add_argument ( '-F', '--fmax',
            help='maximum factor to scan [1.67]',
            type=float, default=1.3 )
    argparser.add_argument ( '-d', '--df',
            help='delta_f [.03]',
            type=float, default=.1 )
    argparser.add_argument ( '-e', '--nevents',
            help='number of events [20000]',
            type=int, default=1000 )
    argparser.add_argument ( '-p', '--picklefile',
            help='pickle file to draw from [%s/hiscore.pcl]' % rundir,
            type=str, default="%s/hiscore.pcl" % rundir )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug, info, warn, err [info]',
            type=str, default="info" )
    args = argparser.parse_args()
    if args.picklefile == "default":
        args.picklefile = "%s/hiscore.pcl" % rundir
    protomodel, trimmed = obtain ( args.number, args.picklefile )
    plotLikelihoodFor ( protomodel, args.pid1, args.pid2, args.fmin, args.fmax, \
                        args.df, args.nevents )

if __name__ == "__main__":
    main()
