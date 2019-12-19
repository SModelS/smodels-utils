#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess, colorama
import setPath
from trimmer import Trimmer
from scipy import stats

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, walkerid, save_hiscores, picklefile="hiscore.pcl" ):
        self.walkerid = walkerid
        self.save_hiscores = save_hiscores
        self.nkeep = 3 ## how many do we keep.
        self.trimmed = [ None ]*self.nkeep
        self.hiscores = [ None ]*self.nkeep
        self.fileAttempts = 0 ## unsucessful attempts at reading or writing
        self.pickleFile = picklefile
        self.mtime = 0 ## last modification time of current list
        self.updateListFromPickle ( )

    def currentMinZ ( self ):
        """ the current minimum Z to make it into the list. """
        if self.hiscores[-1] == None:
            return 0.
        return self.hiscores[-1].Z

    def addResult ( self, protomodel ):
        """ add a result to the list """
        import manipulator
        m = manipulator.Manipulator ( protomodel )
        m.resolveMuhat() ## add only with resolved muhats
        if m.M.Z <= self.currentMinZ():
            return ## doesnt pass minimum requirement
        if m.M.Z == 0.:
            return ## just to be sure, should be taken care of above, though
        if m.M.Z > 2.5:
            ## for values > 2.5 we now predict again with larger statistics.
            m.M.predict ( nevents = 10000 )

        for i,mi in enumerate(self.hiscores):
            if mi!=None and mi.almostSameAs ( m.M ):
                ### this m.M is essentially the m.M in hiscorelist.
                ### Skip!
                self.pprint ( "the protomodel seems to be already in highscore list. skip" )
                return
            if mi!=None and abs ( m.M.Z - mi.Z ) / m.M.Z < 1e-6:
                ## pretty much exactly same score? number of particles wins!!
                if len ( m.M.unFrozenParticles() ) < len ( mi.unFrozenParticles() ):
                    self.demote ( i )
                    self.hiscores[i] = copy.deepcopy ( m.M )
                    self.hiscores[i].clean( all=True )
                    self.trimmed[i] = None
                    break
            if mi==None or m.M.Z > mi.Z: ## ok, <i>th best result!
                self.demote ( i )
                self.hiscores[i] = copy.deepcopy ( m.M )
                self.hiscores[i].clean( all=True )
                self.trimmed[i] = None
                break

    def demote ( self, i ):
        """ demote everything from i+1 on,
            i.e (i+1)->(i+2), (i+2)->(i+3) and so on """
        for j in range(self.nkeep-1,i,-1):
            m = copy.deepcopy ( self.hiscores[j-1] )
            self.hiscores[j]= m
            while len(self.trimmed)<=j:
                self.trimmed.append(None)
            n = copy.deepcopy ( self.trimmed[j-1] )
            self.trimmed[j]= n
        if len(self.hiscores)>self.nkeep:
            self.hiscores = self.hiscores[:self.nkeep]
        if len(self.trimmed)>self.nkeep:
            self.trimmed = self.trimmed[:self.nkeep]
        # assert ( len(self.hiscores) == self.nkeep )

    def updateListFromPickle ( self ):
        """ fetch the list from the pickle file """
        if not os.path.exists ( self.pickleFile ) or \
            os.stat ( self.pickleFile ).st_size < 100:
            return
        mtime = os.stat ( self.pickleFile ).st_mtime
        if mtime > 0 and mtime == self.mtime:
            ## no modification. return
            return

        try:
            with open( self.pickleFile,"rb+") as f:
                fcntl.flock ( f, fcntl.LOCK_EX )
                self.hiscores = pickle.load ( f )
                self.trimmed = pickle.load ( f )
                fcntl.flock ( f, fcntl.LOCK_UN )
            self.mtime = mtime
            nhs, ntr = 0, 0
            for i in self.hiscores:
                if i != None:
                    nhs += 1
            for v in self.trimmed:
                if v != None:
                    ntr += 1
            self.pprint ( "loaded %d hiscores from %s, and %d trimmed ones." % \
                          ( nhs, self.pickleFile, ntr ) )
            # assert ( len(self.hiscores) == self.nkeep )
            self.fileAttempts=0
        except Exception as e:
        # except OSError or BlockingIOError or EOFError or pickle.UnpicklingError or TypeError as e:
            self.fileAttempts+=1
            if self.fileAttempts<20: # try again
                self.pprint ( "Exception %s: Waiting for %s file, %d" % (str(e),self.pickleFile,self.fileAttempts) )
                time.sleep ( (.2 + random.uniform(0.,1.))*self.fileAttempts )
                self.updateListFromPickle()
                self.pprint ( "Loading hiscores worked this time" )
            else:
                self.pprint ( "Timed out when try to get hiscores!" )

    def trimprotomodels ( self, n=None, trimbranchings=False, maxloss=.01 ):
        """ trim the first <n> protomodels in the list """
        if n == None or n < 0 or n > self.nkeep:
            n = self.nkeep
        nevents = 10000
        for i in range(n):
            if self.hiscores[i]!=None:
                trimmer = Trimmer( self.hiscores[i], "aggressive", maxloss,
                                   nevents = nevents )
                trimmer.trim( trimbranchings=trimbranchings )
                while len(self.trimmed)<=i:
                    self.trimmed.append ( None )
                self.trimmed[i] = trimmer.protomodel

    def clean ( self ):
        """ clean hiscore list, i.e. remove cruft from protomodels.
            leave first one as it is """
        for ctr,h in enumerate(self.hiscores[1:]):
            if h != None:
                from manipulator import Manipulator
                m=Manipulator ( h )
                m.resolveMuhat()
                m.M.clean ( all=True )
                self.hiscores[ctr]=m.M

    def save ( self ):
        """ compatibility thing """
        return self.writeListToPickle()

    def writeListToPickle ( self, pickleFile=None ):
        """ dump the list to the pickle file <pickleFile>.
            If pickleFile is None, then self.pickleFile is used.
        """
        if pickleFile==None:
            pickleFile = self.pickleFile
        if os.path.exists ( self.pickleFile ):
            mtime = os.stat ( self.pickleFile ).st_mtime
            if mtime > self.mtime:
                self.pprint ( "while writing to pickle file I see that it has changed" )
                self.updateListFromPickle()
                return False
        self.pprint ( "saving new hiscore list to %s" % pickleFile )
        try:
            subprocess.getoutput ( "mv -f %s old_%s" % ( pickleFile, pickleFile ) )
            self.clean()
            with open( pickleFile, "wb" ) as f:
                fcntl.flock ( f, fcntl.LOCK_EX )
                pickle.dump ( self.hiscores, f )
                pickle.dump ( self.trimmed, f )
                fcntl.flock ( f, fcntl.LOCK_UN )
            self.mtime = os.stat ( self.pickleFile ).st_mtime
            self.fileAttempts=0
            return True
        except OSError or BlockingIOError:
            self.fileAttempts+=1
            if self.fileAttempts<5: # try again
                time.sleep ( .2 )
                self.writeListToPickle( pickleFile )
            return False
        return False

    def newResult ( self, protomodel ):
        """ see if new result makes it into hiscore list. If yes, then add.
        """
        # self.pprint ( "New result with Z=%.2f, %s" % (protomodel.Z, self.save_hiscores ) )
        self.log( "is the new result of walker %d is above threshold: %s > %s?" % \
                  ( protomodel.walkerid, protomodel.Z, self.currentMinZ() ) )
        if not self.save_hiscores:
            return
        if protomodel.Z <= self.currentMinZ():
            return ## clearly out
        ret = False
        ctr = 0
        while not ret:
            self.addResult ( protomodel )
            self.log ( "now save list" )
            ret = self.save() ## and write it
            ctr+=1
            if ctr > 5:
                break
        self.log ( "done saving list" )

    def pprint ( self, *args ):
        """ logging """
        print ( "[hiscore:%d] %s" % ( self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        # logfile = "walker%d.log" % self.walkerid
        logfile = "hiscore.log"
        with open( logfile, "a" ) as f:
            f.write ( "[hiscore:%d - %s] %s\n" % ( self.walkerid, time.asctime(), " ".join(map(str,args)) ) )

def compileList( nmax ):
    """ compile the list from individual hi*pcl """
    import glob
    files = glob.glob ( "H*.pcl" )
    allprotomodels,alltrimmed=[],[]
    print ( "Loading ", end="", flush=True )
    for ctr,fname in enumerate(files):
        s = "."
        if ctr % 100 == 0:
            s = "o"
        elif ctr % 10 == 0:
            s = "x"
        print ( s, end="", flush=True )
        try:
            with open( fname,"rb+") as f:
                fcntl.flock( f, fcntl.LOCK_EX )
                protomodels = pickle.load ( f )
                trimmed = pickle.load ( f )
                fcntl.flock( f, fcntl.LOCK_UN )
                ## add protomodels, but without the Nones
                allprotomodels += list ( filter ( None.__ne__, protomodels ) )
                alltrimmed += list ( filter ( None.__ne__, trimmed ) )
                allprotomodels = sortByZ ( allprotomodels )
                alltrimmed = sortByZ ( alltrimmed )
        except ( IOError, OSError, FileNotFoundError, EOFError, pickle.UnpicklingError ) as e:
            print ( "[hiscore] could not open %s (%s). ignore." % ( fname, e ) )
    print ( )
    if nmax > 0:
        while len(allprotomodels)<nmax:
            allprotomodels.append ( None )
        while len(alltrimmed)<nmax:
            alltrimmed.append ( None )
    return allprotomodels, alltrimmed

def count ( protomodels ):
    return len(protomodels)-protomodels.count(None)

def storeList ( protomodels, trimmed, savefile ):
    """ store the best protomodels in another hiscore file """
    from hiscore import Hiscore
    h = Hiscore ( 0, True, savefile )
    h.hiscores = protomodels
    h.trimmed = trimmed
    print ( "[hiscore] saving %d protomodels and %d trimmed ones to %s" % \
            ( count(protomodels),count(trimmed), savefile ) )
    h.save()

def sortByZ ( protomodels ):
    protomodels.sort ( reverse=True, key = lambda x: x.Z )
    return protomodels[:20] ## only 20

def discuss ( protomodel, name ):
    print ( "Currently %7s Z is: %.3f [%d/%d unfrozen particles, %d predictions] (walker #%d)" % \
            (name, protomodel.Z, len(protomodel.unFrozenParticles()),len(protomodel.masses.keys()),len(protomodel.bestCombo), protomodel.walkerid ) )

def discussBest ( protomodel, detailed ):
    """ a detailed discussion of number 1 """
    p = 1. - stats.norm.cdf ( protomodel.Z )
    print ( "Current           best: %.3f, p=%.2g [%d/%d unfrozen particles, %d predictions] (walker #%d)" % \
            (protomodel.Z, p, len(protomodel.unFrozenParticles()),len(protomodel.masses.keys()),len(protomodel.bestCombo), protomodel.walkerid ) )
    if detailed:
        print ( "Solution was found in step #%d" % protomodel.step )
        for i in protomodel.bestCombo:
            print ( "  prediction in best combo: %s (%s)" % ( i.analysisId(), i.dataType() ) )

def printProtoModels ( protomodels, detailed, nmax=10 ):
    names = { 0: "highest", 1: "second", 2: "third" }
    for c,protomodel in enumerate(protomodels):
        if c >= nmax:
            break
        if protomodel == None:
            break
        sc = "%dth" % (c+1)
        if c in names.keys():
            sc = names[c]
        if c==0:
            discussBest ( protomodel, detailed )
        else:
            discuss ( protomodel, sc )

def produceNewSLHAFileNames ( protomodels, prefix = "cur" ):
    for m in protomodels:
        if m is not None:
            m.createNewSLHAFileName( prefix = prefix )

def main ( args ):
    """ the function that updates the hiscore.pcl file
    :param args: detailed, outfile, infile, print,
                 fetch, nmax, maxloss, trim, trim_branchings,
                 analysis_contributions, check, interactive,
                 see "if __main__" part below.
    :returns: highest significance
    """

    if args.detailed:
        args.print = True
    if args.outfile.lower() in [ "none", "", "false" ]:
        args.outfile = None
    infile = args.infile
    if type(infile) is str and infile.lower() in [ "none", "" ]:
        infile = None
    rundir = "/mnt/hephy/pheno/ww/rundir"
    if os.path.exists ( "rundir.conf" ):
        with open ( "rundir.conf", "rt" ) as f:
            rundir = f.read()
            rundir = rundir.strip()
            rundir = rundir.replace("~",os.environ["HOME"] )
    if infile == "default":
        infile = "%s/hiscore.pcl" % rundir
    if args.outfile == infile:
        print ( "[hiscore] outputfile is same as input file. will assume that you do not want me to write out at all." )
        args.outfile = None

    if args.fetch:
        import subprocess
        cmd = "scp gpu:/local/wwaltenberger/git/sprotomodels-utils/combinations/H*.pcl ."
        print ( "[hiscore] %s" % cmd )
        out = subprocess.getoutput ( cmd )
        print ( out )

    if infile is None:
        protomodels,trimmed = compileList( args.nmax ) ## compile list from H<n>.pcl files
    else:
        with open(infile,"rb+") as f:
            fcntl.flock( f, fcntl.LOCK_EX )
            protomodels = pickle.load ( f )
            trimmed = pickle.load ( f )
            fcntl.flock( f, fcntl.LOCK_UN )

    if protomodels[0] == None:
        print ( "[hiscore] error, we have an empty hiscore list" )
        return 0.

    triZ=0.
    if trimmed[0] != None:
        triZ = trimmed[0].Z
        
    sin = infile
    if sin == None:
        sin = "H*pcl"
    print ( "[hiscore] untrimmed hiscore from %s is at %.2f, trimmed hiscore is at %.2f" % \
            ( sin, protomodels[0].Z, triZ ) ) 

    produceNewSLHAFileNames ( protomodels )
    produceNewSLHAFileNames ( trimmed, prefix="tri" )

    nevents = 20000

    if args.trim:
        protomodel = protomodels[0]
        tr = Trimmer ( protomodel, maxloss=args.maxloss, nevents = nevents )
        tr.trimParticles()
        trimmed[0] = tr.protomodel

    if args.trim_branchings:
        if len(trimmed)>0 and trimmed[0] is not None:
            ## already has a trimmed protomodel? trim only branchings
            protomodel = trimmed[0]
            tr = Trimmer ( protomodel, maxloss = args.maxloss, nevents = nevents )
            tr.trimBranchings()
            trimmed[0] = tr.protomodel
        else:
            protomodel = protomodels[0]
            tr = Trimmer ( protomodel, maxloss = args.maxloss, nevents = nevents )
            tr.trimParticles()
            tr.trimBranchings()
            if len(trimmed)==0:
                trimmed = [ None ]
            trimmed[0] = tr.protomodel

    if args.analysis_contributions:
        protomodel = protomodels[0]
        useTrimmed = False
        if len(trimmed)>0 and trimmed[0] is not None:
            useTrimmed = True
            protomodel = trimmed[0]
        tr = Trimmer ( protomodel, maxloss = args.maxloss, nevents = nevents )
        protomodel = tr.computeAnalysisContributions ()
        if useTrimmed:
            trimmed[0] = protomodel
        else:
            protomodels[0] = protomodel

    if args.nmax > 0:
        protomodels = protomodels[:args.nmax]
        trimmed = trimmed[:args.nmax]

    if args.outfile is not None:
        storeList ( protomodels, trimmed, args.outfile )

    if args.check:
        protomodel = protomodels[0]
        if len(trimmed)>0 and trimmed[0] is not None:
            protomodel = trimmed[0]
        tr = Trimmer ( protomodel, maxloss = args.maxloss, nevents = nevents )
        tr.checkZ()

    if args.print:
        printProtoModels ( trimmed, args.detailed, args.nmax )

    if args.interactive:
        import manipulator
        if len(protomodels)>0 and protomodels[0] != None:
            tr = Trimmer ( protomodels[0], maxloss = args.maxloss, nevents = nevents )
            ma = manipulator.Manipulator ( protomodels[0] )
        print ( "[hiscore] starting interactive session. Variables: %sprotomodels, trimmed%s" % \
                ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( "[hiscore]                                 Modules: %strimmer, manipulator%s" % \
                ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( "[hiscore]                                   Algos: %str, ma%s" % \
                ( colorama.Fore.RED, colorama.Fore.RESET ) )
        import trimmer
        import IPython
        IPython.embed()

    if len(trimmed)>0 and trimmed[0] != None:
        return float(trimmed[0].Z)
    if len(protomodels)>0 and protomodels[0] != None:
        return float(protomodels[0].Z)
    return 0.

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore class. as a commandline tool it allows for '
                        'merging, trimming, printing, and checking of hiscore list' )
    argparser.add_argument ( '-i', '--infile',
            help='Specify the input pickle file to start with. If none, start with H<n>.pcl. [None]',
            type=str, default=None )
    argparser.add_argument ( '-o', '--outfile',
            help='pickle file with hiscores. If none, dont pickle. [hiscore.pcl]',
            type=str, default="hiscore.pcl" )
    argparser.add_argument ( '-n', '--nmax',
            help='maximum number of entries to store [10]',
            type=int, default=10 )
    argparser.add_argument ( '-m', '--maxloss',
            help='maximum loss as a fraction that we allow in trimming [.005]',
            type=float, default=.005 )
    argparser.add_argument ( '-c', '--check',
            help='check if we can reproduce Z value of first entry',
            action="store_true" )
    argparser.add_argument ( '-C', '--analysis_contributions',
            help='compute analysis contributions',
            action="store_true" )
    argparser.add_argument ( '-f', '--fetch',
            help='fetch H<n>.pcl from gpu server',
            action="store_true" )
    argparser.add_argument ( '-t', '--trim',
            help='trim leading protomodel, but only particles', action="store_true" )
    argparser.add_argument ( '-T', '--trim_branchings',
            help='trim leading protomodel, also branchings',
            action="store_true" )
    argparser.add_argument ( '-p', '--print',
            help='print list to stdout', action="store_true" )
    argparser.add_argument ( '-d', '--detailed',
            help='detailed descriptions (requires -p)', action="store_true" )
    argparser.add_argument ( '-I', '--interactive', help='start interactive session',
                             action="store_true" )
    args = argparser.parse_args()

    main ( args )
