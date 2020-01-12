#!/usr/bin/env python3

""" script used to produce the likelihood scans """

import pickle, os, sys, multiprocessing, time
sys.path.insert(0,"./")
from csetup import setup
from combiner import Combiner
from manipulator import Manipulator
from protomodel import predictor as P
from plotHiscore import obtain

def getLikelihoods ( bestcombo, mu = 1. ):
    """ return dictionary with the likelihoods per analysis """
    llhds= {}
    for tp in bestcombo:
        name = "%s:%s:%s" % ( tp.analysisId(), tp.dataId(), ",".join ( [ i.txName for i in tp.txnames ] ) )
        llhds[ name ] = tp.getLikelihood ( mu ) 
    return llhds

def pprint ( *args ):
    """ pretty print """
    t = time.strftime("%H:%M:%S")
    print ( "[llhdscanner:%s] %s" % ( t, " ".join(map(str,args)))  )

def scanLikelihoodFor ( protomodel, pid1, pid2, min1, max1, dm1,
                        min2, max2, dm2, nevents ):
    """ plot the likelihoods as a function of pid1 and pid2 """
    if pid2 != protomodel.LSP:
        print ("[llhdscanner] we currently assume pid2 to be the LSP, but it is %d" % pid2 )
    import numpy
    c = Combiner()
    anaIds = c.getAnaIdsWithPids ( protomodel.bestCombo, [ pid1, pid2 ] )
    ## mass range for pid1
    mpid1 = protomodel.masses[pid1]
    mpid2 = protomodel.masses[pid2]
    rpid1 = numpy.arange ( min1, max1+1e-8, dm1 )
    rpid2 = numpy.arange ( min2, max2+1e-8, dm2 )
    masspoints = []
    print ( "[llhdscanner] range for %d: %d,%d ... %d" % ( pid1, rpid1[0], rpid1[1], rpid1[-1] ) )
    print ( "[llhdscanner] range for %d: %d,%d ... %d" % ( pid2, rpid2[0], rpid2[1], rpid2[-1] ) )
    print ( "[llhdscanner] total %d points, %d events" % ( len(rpid1)*len(rpid2), nevents ) )
    protomodel.createNewSLHAFileName ( prefix="llhd%d" % pid1 )
    protomodel.initializePredictor()
    P[0].filterForAnaIds ( anaIds )
    
    ## first add proto-model point
    protomodel.predict( nevents = nevents, check_thresholds=False, \
                        recycle_xsecs = False )
    mu = 1.
    llhds = getLikelihoods ( protomodel.bestCombo, mu=mu )
    print ( "[llhdscanner] protomodel point: m1,m2,llhds", mpid1, mpid2, llhds, len(protomodel.bestCombo) )
    masspoints.append ( (mpid1,mpid2,llhds) )

    for m1 in rpid1:
        protomodel.masses[pid1]=m1
        protomodel.masses[pid2]=mpid2 ## reset LSP mass
        if hasattr ( protomodel, "stored_xsecs" ):
            del protomodel.stored_xsecs ## make sure we compute
        for i2,m2 in enumerate(rpid2):
            if m2 > m1: ## we assume pid2 to be the daughter
                continue
            protomodel.masses[pid2]=m2
            for pid_,m_ in protomodel.masses.items():
                if pid_ != pid2 and m_ < m2: ## make sure LSP remains the LSP
                    protomodel.masses[pid_]=m2 + 1.
            protomodel.predict( nevents = nevents, check_thresholds=False, \
                                recycle_xsecs = True )
            llhds = getLikelihoods ( protomodel.bestCombo, mu=mu )
            # del protomodel.stored_xsecs ## make sure we compute
            pprint ( "m1,m2,llhds:", m1, m2, llhds, len(protomodel.bestCombo) )
            # print ( )
            masspoints.append ( (m1,m2,llhds) )
    import pickle
    picklefile = "mp%d%d.pcl" % ( pid1, pid2 )
    print ( "[llhdscanner] now saving to %s" % picklefile )
    f=open( picklefile ,"wb" )
    pickle.dump ( masspoints, f )
    pickle.dump ( mpid1, f )
    pickle.dump ( mpid2, f )
    f.close()

def overrideWithDefaults ( args ):
    if not args.defaults:
        return args
    mins = { 1000005:  100., 1000006:  100., 2000006:  100., 1000021:  200. }
    maxs = { 1000005: 1500., 1000006: 1260., 2000006: 1260., 1000021: 2400. }
    dm   = { 1000005:   60., 1000006:   50., 2000006:   50., 1000021:   70. }
    ### make the LSP scan depend on the mother
    LSPmins = { 1000005:   5., 1000006:   5., 2000006:    5., 1000021:    5. }
    LSPmaxs = { 1000005: 800., 1000006: 800., 2000006:  800., 1000021: 2200. }
    LSPdm   = { 1000005:  50., 1000006:  50., 2000006:   50., 1000021:   70. }
    if not args.pid1 in mins:
        print ( "[llhdscanner] asked for defaults for %d, but none defined." % args.pid1 )
        return args
    args.min1 = mins[args.pid1]
    args.max1 = maxs[args.pid1]
    args.deltam1 = dm[args.pid1]
    args.min2 = LSPmins[args.pid1]
    args.max2 = LSPmaxs[args.pid1]
    args.deltam2 = LSPdm[args.pid1]
    return args

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
    argparser.add_argument ( '-m1', '--min1',
            help='minimum mass of pid1 [200.]',
            type=float, default=200. )
    argparser.add_argument ( '-M1', '--max1',
            help='maximum mass of pid1 [2200.]',
            type=float, default=2200. )
    argparser.add_argument ( '-d1', '--deltam1',
            help='delta m of pid1 [100.]',
            type=float, default=50. )
    argparser.add_argument ( '-m2', '--min2',
            help='minimum mass of pid2 [5.]',
            type=float, default=5. )
    argparser.add_argument ( '-M2', '--max2',
            help='maximum mass of pid2 [1800.]',
            type=float, default=1800. )
    argparser.add_argument ( '-d2', '--deltam2',
            help='delta m of pid1 [50.]',
            type=float, default=50. )
    argparser.add_argument ( '-e', '--nevents',
            help='number of events [50000]',
            type=int, default=50000 )
    argparser.add_argument ( '-p', '--picklefile',
            help='pickle file to draw from [%s/hiscore.pcl]' % rundir,
            type=str, default="%s/hiscore.pcl" % rundir )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug, info, warn, err [info]',
            type=str, default="info" )
    argparser.add_argument ( '-d', '--defaults',
            help='use the default ranges for these pids1, overrides min1, max2, etc',
            action="store_true" )
    args = argparser.parse_args()
    if args.picklefile == "default":
        args.picklefile = "%s/hiscore.pcl" % rundir
    protomodel, trimmed = obtain ( args.number, args.picklefile )
    args = overrideWithDefaults ( args )
    scanLikelihoodFor ( protomodel, args.pid1, args.pid2, args.min1, args.max1, \
                        args.deltam1, args.min2, args.max2, args.deltam2, \
                        args.nevents )

if __name__ == "__main__":
    main()
