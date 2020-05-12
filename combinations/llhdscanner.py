#!/usr/bin/env python3

""" script used to produce the likelihood scans """

import pickle, os, sys, multiprocessing, time
sys.path.insert(0,"./")
from smodels.tools.physicsUnits import fb
from csetup import setup
from combiner import Combiner
from manipulator import Manipulator
from protomodel import predictor as P
from plotHiscore import obtain

class Scanner:
    def __init__ ( self, protomodel, pid1, pid2 ):
        self.rundir = setup()
        self.M = protomodel
        self.pid1 = pid1
        self.pid2 = pid2

    def getPredictions ( self, recycle_xsecs = True ):
        """ get predictions, return likelihoods """
        self.M.createSLHAFile( nevents = self.nevents, 
                recycle_xsecs = recycle_xsecs )
        sigmacut=.02*fb
        if max(self.M.masses)>1600:
            sigmacut=.01*fb
        if max(self.M.masses)>1800:
            sigmacut=.003*fb
        if max(self.M.masses)>2000:
            sigmacut=.001*fb
        predictions = P[0].predict ( self.M.currentSLHA, allpreds=True, 
                                     llhdonly=True, sigmacut=sigmacut )
        ## first add proto-model point
        #mu = 1.
        #llhds = self.getLikelihoods ( predictions, mu=mu )
        llhds={}
        import numpy
        for mu in numpy.arange(.4,1.8,.05):
            llhds[float(mu)] = self.getLikelihoods ( predictions, mu=mu )
        return llhds

    def getLikelihoods ( self, predictions, mu = 1. ):
        """ return dictionary with the likelihoods per analysis """
        llhds= {}
        for tp in predictions:
            name = "%s:%s:%s" % ( tp.analysisId(), tp.dataId(), ",".join ( [ i.txName for i in tp.txnames ] ) )
            llhds[ name ] = tp.getLikelihood ( mu ) 
        return llhds

    def pprint ( self, *args ):
        """ pretty print """
        t = time.strftime("%H:%M:%S")
        line = "[llhdscanner:%s] %s" % ( t, " ".join(map(str,args)))
        print ( line )
        with open ( "llhdscan%d.log" % self.pid1, "at" ) as f:
            f.write ( line+"\n" )

    def describeRange ( self, r ):
        """ describe range r in a string """
        if len(r)==0:
            return ""
        if len(r)==1:
            return "%d" % r[0]
        if len(r)==2:
            return "%d,%d" % ( r[0], r[1] )
        return "%d,%d ... %d" % ( r[0], r[1], r[-1] )

    def scanLikelihoodFor ( self, min1, max1, dm1, min2, max2, dm2, 
                            nevents, topo, output ):
        """ plot the likelihoods as a function of pid1 and pid2 
        :param output: prefix for output file [mp]
        """
        self.nevents = nevents
        pid1 = self.pid1
        pid2 = self.pid2
        if pid2 != self.M.LSP:
            print ("[llhdscanner] we currently assume pid2 to be the LSP, but it is %d" % pid2 )
        import numpy
        c = Combiner()
        anaIds = c.getAnaIdsWithPids ( self.M.bestCombo, [ pid1, pid2 ] )
        ## mass range for pid1
        mpid1 = self.M.masses[pid1]
        mpid2 = self.M.masses[pid2]
        rpid1 = numpy.arange ( min1, max1+1e-8, dm1 )
        rpid2 = numpy.arange ( min2, max2+1e-8, dm2 )
        masspoints = []
        print ( "[llhdscanner] range for %d: %s" % ( pid1, self.describeRange( rpid1 ) ) )
        print ( "[llhdscanner] range for %d: %s" % ( pid2, self.describeRange( rpid2 ) ) )
        print ( "[llhdscanner] total %d points, %d events for %s" % ( len(rpid1)*len(rpid2), nevents, topo ) )
        self.M.createNewSLHAFileName ( prefix="llhd%d" % pid1 )
        self.M.initializePredictor()
        P[0].filterForTopos ( topo )
        
        llhds = self.getPredictions ( False )
        self.pprint ( "protomodel point: m1 %d, m2 %d, %d llhds" % \
                      ( mpid1, mpid2, len(llhds) ) )
        masspoints.append ( (mpid1,mpid2,llhds) )
        oldmasses = {}

        if True:
            ## freeze out all other particles
            for pid_,m_ in self.M.masses.items():
                if pid_ not in [ pid1, pid2 ]:
                    self.M.masses[pid_]=1e6

        for m1 in rpid1:
            self.M.masses[pid1]=m1
            self.M.masses[pid2]=mpid2 ## reset LSP mass
            for k,v in oldmasses.items():
                self.pprint ( "WARNING: setting mass of %d back to %d" % ( k, v ) )
                self.M.masses[k]=v
            oldmasses={}
            if hasattr ( self.M, "stored_xsecs" ):
                del self.M.stored_xsecs ## make sure we compute
            for i2,m2 in enumerate(rpid2):
                if m2 > m1: ## we assume pid2 to be the daughter
                    continue
                self.M.masses[pid2]=m2
                for pid_,m_ in self.M.masses.items():
                    if pid_ != pid2 and m_ < m2: ## make sure LSP remains the LSP
                        self.pprint ( "WARNING: have to raise %d from %d to %d" % ( pid_, m_, m2+1. ) )
                        oldmasses[pid_]=m_
                        self.M.masses[pid_]=m2 + 1.
                llhds = self.getPredictions ( True )
                nllhds,nnonzeroes=0,0
                for mu,llhd in llhds.items():
                    nllhds+=len(llhd)
                # del protomodel.stored_xsecs ## make sure we compute
                self.pprint ( "m1 %d, m2 %d, %d mu's, %d llhds." % \
                              ( m1, m2, len(llhds), nllhds ) )
                masspoints.append ( (m1,m2,llhds) )
        import pickle
        picklefile = "%s%d%d.pcl" % ( output, pid1, pid2 )
        self.pprint ( "now saving to %s" % picklefile )
        f=open( picklefile ,"wb" )
        pickle.dump ( masspoints, f )
        pickle.dump ( mpid1, f )
        pickle.dump ( mpid2, f )
        pickle.dump ( nevents, f )
        pickle.dump ( topo, f )
        pickle.dump ( time.asctime(), f )
        f.close()

    def overrideWithDefaults ( self, args ):
        mins = { 1000005:  100., 1000006:  100., 2000006:  100., 1000021:  300., \
                 1000001:  250., 1000002: 250., 1000003: 250., 1000004: 250. }
        maxs = { 1000005: 1500., 1000006: 1260., 2000006: 1260., 1000021: 2351., \
                 1000001: 2051., 1000002: 2051., 1000003: 2051., 1000004: 2051. }
        dm   = { 1000005:    8., 1000006:    8., 2000006:    8., 1000021:   12., \
                 1000001:   10., 1000002:   10., 1000003:   10., 1000004: 10.  }
        topo = { 1000005: "T2bb",1000006: "T2tt", 2000006: "T2tt", 1000021: "T1", \
                 1000001: "T2",  1000002: "T2", 1000003: "T2", 1000004: "T2" }
        ### make the LSP scan depend on the mother
        LSPmins = { 1000005:    5., 1000006:   5., 2000006:    5., 1000021:    5., \
                    1000001:    5., 1000002: 5., 1000003: 5., 1000004: 5. }
        LSPmaxs = { 1000005:  800., 1000006: 800., 2000006:  800., 1000021: 1800., \
                    1000001: 1700., 1000002: 1700., 1000003: 1700., 1000004: 1700. }
        LSPdm   = { 1000005:    8., 1000006:  8., 2000006:   8., 1000021:    12., \
                    1000001:    8., 1000002:   8., 1000003: 8., 1000004: 8. }
        if not args.pid1 in mins:
            print ( "[llhdscanner] asked for defaults for %d, but none defined." % args.pid1 )
            return args
        if args.min1 == None:
            args.min1 = mins[args.pid1]
        if args.max1 == None:
            args.max1 = maxs[args.pid1]
        if args.deltam1 == None:
            args.deltam1 = dm[args.pid1]
        if args.min2 == None:
            args.min2 = LSPmins[args.pid1]
        if args.max2 == None:
            args.max2 = LSPmaxs[args.pid1]
        if args.deltam2 == None:
            args.deltam2 = LSPdm[args.pid1]
        if args.topo == None:
            args.topo = topo[args.pid1]
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
            help='minimum mass of pid1 [None]',
            type=float, default=None )
    argparser.add_argument ( '-M1', '--max1',
            help='maximum mass of pid1 [2200.]',
            type=float, default=None )
    argparser.add_argument ( '-d1', '--deltam1',
            help='delta m of pid1 [None]',
            type=float, default=None )
    argparser.add_argument ( '-m2', '--min2',
            help='minimum mass of pid2 [None]',
            type=float, default=None )
    argparser.add_argument ( '-M2', '--max2',
            help='maximum mass of pid2 [None]',
            type=float, default=None )
    argparser.add_argument ( '-d2', '--deltam2',
            help='delta m of pid1 [None]',
            type=float, default=None )
    argparser.add_argument ( '-t', '--topo',
            help='topology',
            type=str, default=None )
    argparser.add_argument ( '-e', '--nevents',
            help='number of events [50000]',
            type=int, default=50000 )
    argparser.add_argument ( '-p', '--picklefile',
            help='pickle file to draw from [%s/hiscore.pcl]' % rundir,
            type=str, default="%s/hiscore.pcl" % rundir )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug, info, warn, err [info]',
            type=str, default="info" )
    argparser.add_argument ( '-o', '--output',
            help="prefix for output file [mp]",
            type=str, default="mp" )
    args = argparser.parse_args()
    if args.picklefile == "default":
        args.picklefile = "%s/hiscore.pcl" % rundir
    protomodel = obtain ( args.number, args.picklefile )
    scanner = Scanner( protomodel, args.pid1, args.pid2 )
    args = scanner.overrideWithDefaults ( args )
    scanner.scanLikelihoodFor ( args.min1, args.max1, args.deltam1, 
                                args.min2, args.max2, args.deltam2, \
                                args.nevents, args.topo, args.output )

if __name__ == "__main__":
    main()
