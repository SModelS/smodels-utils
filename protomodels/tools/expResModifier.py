#!/usr/bin/env python3

""" a simple class that performs global modifications on a list of results.
Used to ``take out potential signals'' i.e. put all observations to values
expected from background, by sampling the background model. """

# https://link.springer.com/content/pdf/10.1007/JHEP02(2015)004.pdf

import copy, os, sys, time, subprocess, math
sys.path.insert( 0, "../" )
sys.path.insert(0,"/scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/protomodels/")
from scipy import stats
from builder.protomodel import ProtoModel
from builder.manipulator import Manipulator
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.model import Model
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.tools.simplifiedLikelihoods import Data, UpperLimitComputer
from smodels.theory import decomposer
from tools.csetup import setup

class ExpResModifier:
    def __init__ ( self, dbpath, Zmax, rundir, keep, nproc, fudge ):
        """
        :param dbpath: path to database
        :param Zmax: upper limit on an individual excess
        """
        self.dbpath = dbpath
        self.protomodel = None
        self.rundir = setup( rundir )
        self.keep = keep
        self.nproc = nproc
        self.fudge = fudge
        self.logfile = "modifier.log"
        if Zmax == None:
            Zmax = 100
        self.Zmax = Zmax
        self.startLogger()
        self.stats = {}

    def interact ( self, listOfExpRes ):
        import IPython
        IPython.embed( using=False )

    def computeNewObserved ( self, txname, globalInfo ):
        """ given expected upper limit, compute a fake observed limit
            by sampling the non-truncated Gaussian likelihood """
        expected = txname.txnameDataExp
        observed = txname.txnameData
        ## we only draw once for the entire UL map, equivalent to assuming
        ## that we are dealing with only one signal region
        ## second basic assumption: sigma_obs approx sigma_exp
        allpositive = False
        ctr = 0
        x = float("inf")
        ## stop when all values are positive
        while not allpositive:
            ret = copy.deepcopy ( expected )
            ctr += 1
            x = float("inf")
            D = {}
            while x > self.Zmax:
                x = stats.norm.rvs() * self.fudge # draw but once from standard-normal
                D["x"] = x
            allpositive = True
            for i,y in enumerate( ret.y_values ):
                sigma_exp = y / 1.96 ## the sigma of the Gaussian
                D["yexp"]= y
                D["yobs"]= float("nan") 
                if len(ret.y_values) == len(observed.y_values):
                    D["yobs"]=observed.y_values[i]
                D["sigma_exp"]= sigma_exp
                ## now lets shift, observed limit = expected limit + dx
                obs = y + sigma_exp * x ## shift the expected by the random fake signal
                D["y"]= obs ## we keep only last entry, but thats ok
                if obs <= 0.:
                    ## try again
                    allpositive = False
                ret.y_values[i] = obs ## now we simply shift
            if ctr > 2:
                self.log ( "WARNING seems like I am having a hard time getting all "\
                        "values of %s positive." % globalInfo.id )

        label = globalInfo.id + ":ul"
        D["fudge"]=self.fudge
        self.stats[label]=D
        self.log ( "fixing UL result %s: x=%.2f" % \
                   ( globalInfo.id, x ) )
        if x > 3.5:
            self.log ( "WARNING high UL x=%.2f!!!" % x )
        return ret

    def bgUpperLimit ( self, dataset ):
        """ fix the upper limits, use expected (if exists) as observed """
        ## FIXME wherever possible, we should sample from the non-truncated likelihood, take that as the signal strength and re-computed a likelihood with it.
        for i,txname in enumerate(dataset.txnameList):
            if hasattr ( txname, "txnameDataExp" ) and txname.txnameDataExp != None:
                txnd = self.computeNewObserved ( txname, dataset.globalInfo )
                dataset.txnameList[i].txnameData = txnd
        return dataset

    def pprint ( self, *args ):
        """ logging """
        print ( "[expResModifier] %s" % ( " ".join(map(str,args))) )
        with open( self.logfile, "a" ) as f:
            f.write ( "[modifier] %s\n" % ( " ".join(map(str,args)) ) )

    def startLogger ( self ):
        subprocess.getoutput ( "mv %s modifier.old" % self.logfile )
        self.log ( "starting at %s with zmax of %s" % \
                   ( time.asctime(), self.Zmax ) )
        self.log ( "arguments were %s" % ( " ".join ( sys.argv ) ) )

    def log ( self, *args ):
        """ logging to file """
        # logfile = "walker%d.log" % self.walkerid
        with open( self.logfile, "a" ) as f:
            f.write ( "[modifier] %s\n" % ( " ".join(map(str,args)) ) )

    def finalize ( self ):
        """ finalize, for the moment its just deleting slha files """
        print ( "[expResModifier] finalize" )
        if self.keep:
            return
        if hasattr ( self, "protomodel" ) and self.protomodel is not None:
            self.protomodel.delCurrentSLHA()

    def produceProtoModel ( self, filename, dbversion ):
        """ try to produce a protomodel from pmodel
        :param filename: filename of pmodel dictionary
        :param dbversion: version of database, for tracking
        :returns: none if not succesful, else protomodel object
        """
        if filename == "":
            return None
        if not os.path.exists ( filename ):
            self.pprint ( "When trying to construct protomodel, %s does not exist" % filename )
            return None
        walkerid = 0
        expected = False
        select = "all"
        keep_meta = True
        # M = ProtoModel ( walkerid, self.dbpath, expected, select, keep_meta )
        M = ProtoModel ( walkerid, keep_meta, dbversion = dbversion )
        M.createNewSLHAFileName ( prefix="erm" )
        ma = Manipulator ( M )
        with open ( filename, "rt" ) as f:
            m = eval ( f.read() )
        ma.initFromDict ( m )
        ma.M.computeXSecs( keep_slha = True )
        self.log ( f"xsecs produced {ma.M.currentSLHA}" )
        self.log ( " `- does currentslha exist? %s" % \
                   os.path.exists ( ma.M.currentSLHA ) )
        ma.printXSecs()
        self.protomodel = ma.M
        return self.protomodel

    def modifyDatabase ( self, outfile="", suffix="fake1", pmodel="" ):
        """ modify the database, possibly write out to a pickle file
        :param outfile: if not empty, write the database into file
        :param suffix: suffix to append to database version
        :param pmodel: if not empty, then this is the file name of the signal
                       model. in this case fake a signal
        :returns: the database
        """
        self.suffix = suffix
        self.log ( "starting to create %s. suffix is %s protomodel is %s." % \
                   ( outfile, suffix, pmodel ) )
        db = Database ( self.dbpath )
        self.dbversion = db.databaseVersion
        # listOfExpRes = db.getExpResults( useSuperseded=True, useNonValidated=True )
        listOfExpRes = db.expResultList ## seems to be the safest bet?
        self.produceProtoModel ( pmodel, db.databaseVersion )
        # print ( "pm produced", os.path.exists ( self.protomodel.currentSLHA ) )
        self.log ( "%d results before faking bgs" % len(listOfExpRes) )
        updatedListOfExpRes = self.fakeBackgrounds ( listOfExpRes )
        # print ( "fb produced", os.path.exists ( self.protomodel.currentSLHA ) )
        self.log ( "%d results after faking bgs" % len(updatedListOfExpRes) )
        updatedListOfExpRes = self.addSignals ( updatedListOfExpRes )
        self.log ( "%d results after adding signals" % len(updatedListOfExpRes) )
        db.expResultList = updatedListOfExpRes
        newver = db.databaseVersion + suffix
        db.txt_meta.databaseVersion = newver
        db.pcl_meta.databaseVersion = newver
        self.pprint ( "Constructed fake database with %d (of %d) results" % \
                ( len(updatedListOfExpRes), len(listOfExpRes) ) )
        if outfile != "":
            db.createBinaryFile( outfile )
        return db

    def sampleEfficiencyMap ( self, dataset ):
        """ for the given dataset,
        sample from background and put the value as observed """
        orig = dataset.dataInfo.observedN
        exp = dataset.dataInfo.expectedBG
        err = dataset.dataInfo.bgError * self.fudge
        D = { "origN": orig, "expectedBG": exp, "bgError": err, "fudge": self.fudge }
        S, origS = float("inf"), float("nan")
        while S > self.Zmax:
            lmbda = stats.norm.rvs ( exp, err )
            dataset.dataInfo.lmbda = lmbda
            if lmbda < 0.:
                lmbda = 0.
            obs = stats.poisson.rvs ( lmbda )
            toterr = math.sqrt ( err**2 + exp )
            S, origS = 0., 0.
            if toterr > 0.:
                S = ( obs - exp ) / toterr
                origS = ( orig - exp ) / toterr
            if S < self.Zmax:
                self.log ( "effmap replacing old nobs=%d (bg=%.2f+/-%.2f, lmbda=%.2f, S=%.2f) with nobs=%d for %s" % \
                    ( orig, err, exp, lmbda, S, obs, dataset.globalInfo.id ) )
                dataset.dataInfo.observedN = obs
        if S > 3.5:
            self.log ( "WARNING!!! high em S=%.2f!!!!" % S )
        D["S"]=S
        D["origS"]=origS
        D["lmbda"]=lmbda
        D["newObs"]=obs
        D["toterr"]=toterr
        ## origN stores the n_observed of the original database
        dataset.dataInfo.origN = orig
        label = dataset.globalInfo.id + ":" + dataset.dataInfo.dataId
        self.stats[ label ] = D
        return dataset

    def addSignalForEfficiencyMap ( self, dataset, tpred, lumi ):
        """ add a signal to this efficiency map. background sampling is
            already taken care of """
        self.log ( "add EM matching tpred %s/%s: %s" % \
                ( tpred.analysisId(), tpred.dataId()[:8], tpred.xsection.value ) )
        label = dataset.globalInfo.id + ":" + dataset.dataInfo.dataId
        if not label in self.stats:
            self.stats[ label ]= {}
        orig = dataset.dataInfo.observedN
        sigLambda = float ( tpred.xsection.value * lumi )
        self.stats[label]["sigLambda"]=sigLambda
        sigN = stats.poisson.rvs ( sigLambda )
        self.stats[label]["sigN"]=sigN
        err = dataset.dataInfo.bgError * self.fudge
        if sigN == 0:
                self.log ( " `- signal sigN=%d re obsN=%d too small. skip." % \
                           ( sigN, orig ) )
                dataset.dataInfo.origUpperLimit = dataset.dataInfo.upperLimit
                dataset.dataInfo.origExpectedUpperLimit = dataset.dataInfo.expectedUpperLimit
                return dataset
        ## the signal is less than permille of bg?
        if orig > 0. and sigN / orig < 1e-3:
                self.log ( " `- signal sigN=%d re obsN=%d too small. skip." % \
                           ( sigN, orig ) )
                dataset.dataInfo.origUpperLimit = dataset.dataInfo.upperLimit
                dataset.dataInfo.origExpectedUpperLimit = dataset.dataInfo.expectedUpperLimit
                return dataset
        self.log ( " `- effmap adding sigN=%d to obsN=%d" % \
                   ( sigN, orig ) )
        dataset.dataInfo.trueBG = orig ## keep track of true bg
        dataset.dataInfo.observedN = orig + sigN
        dataset.dataInfo.sigN = sigN ## keep track of signal

        ## now recompute the limits!!
        alpha = .05
        if orig == 0.0:
            orig = 0.00001
        computer = UpperLimitComputer(cl=1.-alpha )
        m = Data( orig+sigN, orig, err**2, nsignal = 1. )
        lumi = dataset.globalInfo.lumi# .asNumber(1./fb)
        maxSignalXsec = computer.ulSigma(m, marginalize=True ) / lumi
        dataset.dataInfo.origUpperLimit = dataset.dataInfo.upperLimit
        dataset.dataInfo.origExpectedUpperLimit = dataset.dataInfo.expectedUpperLimit
        dataset.dataInfo.upperLimit = maxSignalXsec
        maxSignalXsec = computer.ulSigma(m, marginalize=True, expected=True ) / lumi
        dataset.dataInfo.expectedUpperLimit = maxSignalXsec

        return dataset

    def txNameIsIn ( self, txname, tpred ):
        """ check if txname is in tpred
        :param txname: a txName object
        :param tpred: a theoryPred object
        """
        for txn in tpred.txnames:
            if txn.txName == txname.txName:
                return True
        return False

    def addSignalForULMap ( self, dataset, tpred, lumi ):
        """ add a signal to this UL result. background sampling is
            already taken care of """
        self.log ( " `- add UL matching tpred %s: %s[%s]" % \
                ( tpred.analysisId(), tpred.xsection.value, \
                  tpred.PIDs ) )
        #print ( " `- add UL matching tpred %s: %s[%s] ds:%s" % \
        #        ( tpred.analysisId(), tpred.xsection.value, \
        #          tpred.PIDs, dataset ) )
        ## so we simply add the theory predicted cross section to the limit
        sigmaN = tpred.xsection.value.asNumber(fb)
        ## sigmaN is the predicted production cross section of the signal,
        ## in fb
        def distance ( v1, v2 ):
            """ compute distance between v1 and v2 """
            ret = 0.
            v1,v2 = list(v1),list(v2)
            if len(v1)*2 == len(v2):
                v1 = v1*2
            for _1,_2 in zip ( v1, v2 ):
                ret+= ( _1 - _2 )**2
            ret = math.sqrt (ret )
            return ret

        for i,txname in enumerate(dataset.txnameList):
            if not self.txNameIsIn ( txname, tpred ):
                continue
            #print ( "  `-- adding %s to %s" % ( sigmaN, txname ) )
            txnd = txname.txnameData
            etxnd = txname.txnameDataExp
            coordsTpred = txnd.dataToCoordinates ( tpred.mass ) ## coordinates of tpred
            for yi,y in enumerate(txnd.y_values):
                pt = txnd.tri.points[yi] ## the point in the rotated coords
                dist = distance ( pt, coordsTpred )
                if dist > 400.: ## change y_values only in vicinity of protomodel
                    continue
                oldv = txnd.y_values[yi]
                if etxnd != None and len(txnd.y_values) == len(etxnd.y_values):
                    dt = ( ( txnd.delta_x - etxnd.delta_x )**2 ).sum()
                    if dt < 1e-2:
                        oldv = etxnd.y_values[yi] ## FIXME more checks pls
                # print ( "    `--- adding %s %s" % ( oldv, sigmaN ) )
                txnd.y_values[yi]=oldv + sigmaN
            dataset.txnameList[i].txnameData = txnd
            dataset.txnameList[i].sigmaN = sigmaN
        return dataset

    def saveStats ( self ):
        """ write out the collected stats, so we can discuss experimentalists'
            conservativeness """
        filename = "%s/db%s.dict" % ( self.rundir, self.suffix )
        self.log ( f"saving stats to {filename}" )
        meta = { "dbpath": self.dbpath, "Zmax": self.Zmax,
                 "database": self.dbversion, "fudge": self.fudge,
                 "protomodel": self.protomodel, "timestamp": time.asctime() }
        with open ( filename,"wt" ) as f:
            f.write ( str(meta)+"\n" )
            f.write ( str(self.stats)+"\n" )
            f.close()

    def produceTopoList ( self ):
        """ create smstopolist """
        model = Model ( BSMList, SMList )
        model.updateParticles ( inputFile=self.protomodel.currentSLHA )
        mingap=10*GeV
        sigmacut = 0.02*fb
        self.topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )

    def addSignalsSingleProc ( self, listOfExpRes ):
        """ thats the method that adds a typical signal """
        # print ( "adding signals", os.path.exists ( self.protomodel.currentSLHA ) )
        if self.protomodel == None:
            return listOfExpRes
        ret = []
        self.produceTopoList()
        self.log ( "now add the signals from %s, %d topos" % \
                   ( self.getPModelName(), len(self.topos) ) )
        addedUL, addedEM = 0, 0
        print ( f"{len(listOfExpRes)} results: ", end="" )
        for l,expRes in enumerate(listOfExpRes):
            print ( ".", flush=True, end="" )
            tpreds = theoryPredictionsFor ( expRes, self.topos, useBestDataset=False,
                                            combinedResults=False )
            if tpreds == None:
                ret.append ( expRes )
                continue
            lumi = expRes.globalInfo.lumi
            #self.pprint ( "adding a signal for %s (lumi %s)" % \
            #              ( expRes.id(), lumi ) )
            for i,dataset in enumerate(expRes.datasets):
                dt = dataset.dataInfo.dataType
                dsname = dataset.dataInfo.dataId
                if dt == "upperLimit":
                    for tpred in tpreds:
                        if tpred.dataId() == None:
                            # IPython.embed()
                            addedUL += 1
                            listOfExpRes[l].datasets[i] = self.addSignalForULMap ( dataset, tpred, lumi )
                else:
                    for tpred in tpreds:
                        if tpred.dataId() == dsname:
                            addedEM += 1
                            listOfExpRes[l].datasets[i] = self.addSignalForEfficiencyMap ( dataset, tpred, lumi )
                    ## expRes.datasets[i] = self.fixUpperLimit ( dataset )
        print ( )
        self.log ( f"added {addedUL} UL signals and {addedEM} EM signals" )
        return listOfExpRes

    def signalAdder ( self, listOfExpRes ):
        # print ( "[expResModifier] signalAdder", len(listOfExpRes), len(self.topos) )
        addedUL, addedEM = 0, 0
        for l,expRes in enumerate(listOfExpRes):
            print ( ".", flush=True, end="" )
            tpreds = theoryPredictionsFor ( expRes, self.topos, useBestDataset=False,
                                            combinedResults=False )
            if tpreds == None:
                # ret.append ( expRes )
                continue
            lumi = expRes.globalInfo.lumi
            #self.pprint ( "adding a signal for %s (lumi %s)" % \
            #              ( expRes.id(), lumi ) )
            for i,dataset in enumerate(expRes.datasets):
                dt = dataset.dataInfo.dataType
                dsname = dataset.dataInfo.dataId
                if dt == "upperLimit":
                    for tpred in tpreds:
                        if tpred.dataId() == None:
                            # IPython.embed()
                            addedUL += 1
                            listOfExpRes[l].datasets[i] = self.addSignalForULMap ( dataset, tpred, lumi )
                else:
                    for tpred in tpreds:
                        if tpred.dataId() == dsname:
                            addedEM += 1
                            listOfExpRes[l].datasets[i] = self.addSignalForEfficiencyMap ( dataset, tpred, lumi )
                    ## expRes.datasets[i] = self.fixUpperLimit ( dataset )
        self.log ( f"added {addedUL} UL signals and {addedEM} EM signals" )
        return listOfExpRes

    def getPModelName ( self ):
        """ name of protomodel """
        pmodelname = str(self.protomodel)
        for i in [ "<sub>", "<sup>", "</sub>", "</sup>" ]:
            pmodelname = pmodelname.replace( i, "" )
        return pmodelname

    def addSignals ( self, listOfExpRes ):
        """ thats the method that adds a typical signal, parallel version
        :param nproc: number of processes
        """
        if self.protomodel == None:
            return listOfExpRes
        if self.nproc == 1:
            return self.addSignalsSingleProc ( listOfExpRes )
        # print ( "adding signals", os.path.exists ( self.protomodel.currentSLHA ) )
        ret = []
        self.produceTopoList()
        self.log ( "now add the signals from %s, K=%s, %d topos, %d procs" % \
                   ( self.getPModelName(), len(self.topos), self.nproc ) )
        import multiprocessing
        ## listOfExpRes=listOfExpRes[:10]
        chunks = [ listOfExpRes[i::self.nproc] for i in range(self.nproc) ]
        pool = multiprocessing.Pool ( processes = self.nproc )
        tmp = pool.map ( self.signalAdder, chunks )
        print ( "done! now collect." )
        ret = []
        for t in tmp:
            for x in t:
                ret.append ( x )
        ## print ( "ret=", ret )
        return ret

    def fakeBackgrounds ( self, listOfExpRes ):
        """ thats the method that samples the backgrounds """
        ret = []
        self.log ( "now fake backgrounds" )
        for expRes in listOfExpRes:
            for i,dataset in enumerate(expRes.datasets):
                dt = dataset.dataInfo.dataType
                if dt == "upperLimit":
                    expRes.datasets[i] = self.bgUpperLimit ( dataset )
                elif dt == "efficiencyMap":
                    expRes.datasets[i] = self.sampleEfficiencyMap ( dataset )
                else:
                    print ( "[expResModifier] dataset type %s unknown" % dt )
            ret.append ( expRes )
        self.log ( "done faking the backgrounds" )
        return ret

    def upload( self ):
        import filecmp
        # cmd = "cp %s ./modifier.log %s" % ( args.outfile, self.rundir )
        for f in [ args.outfile, self.logfile ]:
            if not filecmp.cmp ( f, self.rundir+"/"+os.path.basename ( f ) ):
                cmd = f"cp {f} {self.rundir}"
                a = subprocess.getoutput ( cmd )
                print ( "[expResModifier]", cmd, a )
        fname = f"{self.rundir}/default.pcl"
        if os.path.exists ( fname ):
            cmd = f"rm {fname}"
            a = subprocess.getoutput ( cmd )
            print ( "[expResModifier]", cmd, a )
        cmd = "ln -s %s/%s %s/default.pcl" % ( self.rundir, args.outfile, self.rundir )
        a = subprocess.getoutput ( cmd )
        print ( "[expResModifier]", cmd, a )

def check ( picklefile ):
    """ check the picklefile """
    print ( "now checking the modified database" )
    db = Database ( picklefile )
    listOfExpRes = db.getExpResults()
    for er in listOfExpRes:
        datasets = er.datasets
        for ds in datasets:
            txnl = ds.txnameList
            for txn in txnl:
                x = txn.txnameData.dataType
    print ( "were good", db.databaseVersion )


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
                        description='experimental results modifier. used to take out potential signals from the database by setting all observations to values sampled from the background expectations. can insert signals, too.',
                        epilog='./expResModifier.py -R $RUNDIR -d original.pcl -s signal1 -P pmodel9.py' )
    argparser.add_argument ( '-d', '--database',
            help='database to use [../../smodels-database]',
            type=str, default="../../smodels-database" )
    argparser.add_argument ( '-o', '--outfile',
            help='file to write out database pickle. If left empty, then outfile is <suffix>.pcl [""]',
            type=str, default="" )
    argparser.add_argument ( '-s', '--suffix',
            help='suffix for database version ["fake1"]',
            type=str, default="fake1" )
    argparser.add_argument ( '-R', '--rundir',
            help='override rundir [None]',
            type=str, default=None )
    argparser.add_argument ( '-f', '--fudge',
            help='fudge factor [1.0]',
            type=float, default=1.0 )
    argparser.add_argument ( '-M', '--max',
            help='upper limit on significance of individual excess [None]',
            type=float, default=None )
    argparser.add_argument ( '-N', '--nproc',
            help='number of parallel processes, for signal adding [1]',
            type=int, default=1 )
    argparser.add_argument ( '-P', '--pmodel',
            help='supply filename of a pmodel, in which case create a signal-infused database [""]',
            type=str, default="" )
    argparser.add_argument ( '-v', '--verbose',
            help='print results to stdout', action='store_true' )
    argparser.add_argument ( '-I', '--interactive',
            help='interactive mode', action='store_true' )
    argparser.add_argument ( '-B', '--build',
            help='build the original pickle file with all relevant info, then exit (use --database to specify path)', action='store_true' )
    argparser.add_argument ( '-c', '--check',
            help='check the pickle file <outfile>', action='store_true' )
    argparser.add_argument ( '-u', '--upload',
            help='upload to $RUNDIR', action='store_true' )
    argparser.add_argument ( '-k', '--keep',
            help='keep temporary files (for debugging)', action='store_true' )
    args = argparser.parse_args()
    if args.build:
        from smodels.experiment.txnameObj import TxNameData
        TxNameData._keep_values = True
        from smodels.experiment.databaseObj import Database
        print ( f"[expResModifier] starting to build database at {args.database}." )
        db = Database ( args.database )
        print ( f"[expResModifier] built database at {args.database}. Exiting." )
        sys.exit()
    if type(args.rundir)==str and not "/" in args.rundir:
        args.rundir = "/scratch-cbe/users/wolfgan.waltenberger/" + args.rundir
    if args.outfile == "":
        args.outfile = args.suffix+".pcl"
    from smodels.experiment.databaseObj import Database
    modifier = ExpResModifier( args.database, args.max, args.rundir, args.keep, \
                               args.nproc, args.fudge )
    if not args.outfile.endswith(".pcl"):
        print ( "[expResModifier] warning, shouldnt the name of your outputfile ``%s'' end with .pcl?" % args.outfile )
    er = modifier.modifyDatabase ( args.outfile, args.suffix, args.pmodel )

    modifier.saveStats()

    if args.check:
        check ( args.outfile )

    if args.interactive:
        modifier.interact ( er )

    if args.upload:
        modifier.upload()

    modifier.finalize()
