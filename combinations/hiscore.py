#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess, colorama, sys
import setPath
from helpers import rthresholds
from scipy import stats

def setup():
    # codedir = "/mnt/hephy/pheno/ww/git/"
    codedir = "/scratch-cbe/users/wolfgan.waltenberger/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    # rundir = "/mnt/hephy/pheno/ww/rundir/"
    rundir = "/scratch-cbe/users/wolfgan.waltenberger/rundir/"
    # rundir = "./"
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
    rundir = rundir.replace ( "~", os.environ["HOME"] )
    os.chdir ( rundir )
    return rundir

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, walkerid, save_hiscores, picklefile="hiscore.pcl",
                   backup=True, hiscores=None ):
        """ the constructor
        :param save_hiscores: if true, then assume you want to save, not just read.
        :param picklefile: path of pickle file name to connect hiscore list with
        :param backup: if True, make a backup pickle file old_<name>.pcl
        :param hiscores: if None, try to get them from file, if a list, 
                         then these are the hiscore protomodels.
        """
        self.walkerid = walkerid
        self.save_hiscores = save_hiscores
        self.backup = backup ## backup hiscore lists?
        self.nkeep = 3 ## how many do we keep.
        self.hiscores = [ None ]*self.nkeep
        self.fileAttempts = 0 ## unsucessful attempts at reading or writing
        self.pickleFile = picklefile
        self.mtime = 0 ## last modification time of current list
        if hiscores == None:
            self.updateListFromPickle ( )
        else:
            self.hiscores = hiscores
            self.mtime = time.time()

    def currentMinZ ( self ):
        """ the current minimum Z to make it into the list. """
        if self.hiscores[-1] == None:
            return 0.
        return self.hiscores[-1].Z

    def currentMinK ( self ):
        """ the current minimum K to make it into the list. """
        if self.hiscores[-1] == None:
            return -30.
        return self.hiscores[-1].K

    def globalMaxZ ( self ):
        """ globally (across all walkers), the highest Z """
        ret = 0.
        if self.hiscores[0] != None:
            if self.hiscores[0].Z > ret:
                ret = self.hiscores[0].Z
        Zoldfile = "Zold.conf"
        if os.path.exists ( Zoldfile ):
            with open ( Zoldfile, "rt" ) as f:
                lines = f.readlines()
                if len(lines)>0:
                    ret = float(lines[0])
                f.close()
        return ret

    def globalMaxK ( self ):
        """ globally (across all walkers), the highest K """
        ret = 0.
        if self.hiscores[0] != None:
            if self.hiscores[0].K > ret:
                ret = self.hiscores[0].K
        Koldfile = "Kold.conf"
        if os.path.exists ( Koldfile ):
            with open ( Koldfile, "rt" ) as f:
                lines = f.readlines()
                if len(lines)>0:
                    ret = float(lines[0])
                f.close()
        return ret

    def addResult ( self, protomodel ):
        """ add a result to the list """
        import manipulator
        m = manipulator.Manipulator ( protomodel )
        m.resolveMuhat() ## add only with resolved muhats
        if m.M.K <= self.currentMinK():
            return ## doesnt pass minimum requirement
        if m.M.K == 0.:
            return ## just to be sure, should be taken care of above, though
        if m.M.K > 5.:
            ## for values > 2.5 we now predict again with larger statistics.
            m.predict ()

        Zold = self.globalMaxZ()
        Kold = self.globalMaxK()

        if m.M.K > Kold:
            ## we have a new hiscore?
            ## compute the particle contributions
            m.computeParticleContributions()
            ## compute the analysis contributions
            m.computeAnalysisContributions()

        for i,mi in enumerate(self.hiscores):
            if mi!=None and mi.almostSameAs ( m.M ):
                ### this m.M is essentially the m.M in hiscorelist.
                ### Skip!
                self.pprint ( "the protomodel seems to be already in highscore list. skip" )
                return
            if mi!=None and abs ( m.M.K - mi.K ) / m.M.K < 1e-6:
                ## pretty much exactly same score? number of particles wins!!
                if len ( m.M.unFrozenParticles() ) < len ( mi.unFrozenParticles() ):
                    self.demote ( i )
                    self.hiscores[i] = copy.deepcopy ( m.M )
                    self.hiscores[i].clean( all=True )
                    break
            if mi==None or m.M.K > mi.K: ## ok, <i>th best result!
                self.demote ( i )
                self.hiscores[i] = copy.deepcopy ( m.M )
                self.hiscores[i].clean( all=True )
                break

    def addResultByZ ( self, protomodel ):
        """ add a result to the list, old version,
            sort by Z """
        import manipulator
        m = manipulator.Manipulator ( protomodel )
        m.resolveMuhat() ## add only with resolved muhats
        if m.M.Z <= self.currentMinZ():
            return ## doesnt pass minimum requirement
        if m.M.Z == 0.:
            return ## just to be sure, should be taken care of above, though
        if m.M.Z > 2.8:
            ## for values > 2.5 we now predict again with larger statistics.
            m.predict ()

        Zold = self.globalMaxZ()
        Kold = self.globalMaxK()

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
                    break
            if mi==None or m.M.Z > mi.Z: ## ok, <i>th best result!
                self.demote ( i )
                self.hiscores[i] = copy.deepcopy ( m.M )
                self.hiscores[i].clean( all=True )
                break

    def demote ( self, i ):
        """ demote everything from i+1 on,
            i.e (i+1)->(i+2), (i+2)->(i+3) and so on """
        for j in range(self.nkeep-1,i,-1):
            m = copy.deepcopy ( self.hiscores[j-1] )
            self.hiscores[j]= m
        if len(self.hiscores)>self.nkeep:
            self.hiscores = self.hiscores[:self.nkeep]

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
            with open( self.pickleFile,"rb") as f:
                try:
                    #fcntl.flock ( f, fcntl.LOCK_EX | fcntl.LOCK_NB )
                    self.hiscores = pickle.load ( f )
                    self.timestamp = "?"
                    try:
                        self.timestamp = pickle.load ( f )
                    except EOFError as e:
                        pass
                    #fcntl.flock ( f, fcntl.LOCK_UN )
                    f.close()
                except (BlockingIOError,OSError) as e:
                    ## make sure we dont block!
                    #fcntl.flock( f, fcntl.LOCK_UN )
                    raise e
            self.mtime = mtime
            nhs = 0
            for i in self.hiscores:
                if i != None:
                    nhs += 1
            self.pprint ( "loaded %d hiscores from %s." % \
                          ( nhs, self.pickleFile ) )
            # assert ( len(self.hiscores) == self.nkeep )
            self.fileAttempts=0
        except Exception as e:
        # except OSError or BlockingIOError or EOFError or pickle.UnpicklingError or TypeError as e:
            self.fileAttempts+=1
            if self.fileAttempts<20: # try again
                self.pprint ( "Exception[X] %s: type(%s), Waiting for %s file, %d" % (str(e),type(e),self.pickleFile,self.fileAttempts) )
                time.sleep ( (.2 + random.uniform(0.,1.))*self.fileAttempts )
                self.updateListFromPickle()
                self.pprint ( "Loading hiscores worked this time" )
            else:
                self.pprint ( "Timed out when try to get hiscores!" )

    def clean ( self ):
        """ clean hiscore list, i.e. remove cruft from protomodels.
            leave first one as it is """
        for ctr,h in enumerate(self.hiscores[1:]):
            if h != None:
                from manipulator import Manipulator
                m=Manipulator ( h )
                m.resolveMuhat()
                m.M.clean ( all=True )
                self.hiscores[ctr+1]=m.M

    def writeListToDictFile ( self, dictFile=None ):
        """ write the models in append mode in a single dictFile.
        :param dictFile: write to dictFile. If None, then self.pickleFile
                         is used, but with ".dict" as extension.
        """
        if dictFile==None:
            dictFile = self.pickleFile
        if dictFile.endswith(".pcl"):
            dictFile = dictFile[:-4]+".dict"
        f=open(dictFile,"wt")
        f.write("[")
        f.close()
        from manipulator import Manipulator
        for protomodel in self.hiscores:
            ma = Manipulator ( protomodel )
            ma.writeDictFile ( outfile = dictFile, appendMode=True )
        f=open(dictFile,"at")
        f.write("]\n")
        f.close()

    def writeListToPickle ( self, pickleFile=None, check=True ):
        """ pickle the hiscore list.
        :param pickleFile: write to pickleFile. If None, then self.pickleFile
            is used.
        :param check: perform a check whether the file has changed?
        """
        if pickleFile==None:
            pickleFile = self.pickleFile
        if check and os.path.exists ( self.pickleFile ):
            mtime = os.stat ( self.pickleFile ).st_mtime
            if mtime > self.mtime:
                self.pprint ( "while writing to pickle file I see that it has changed" )
                self.updateListFromPickle()
                return False
        self.pprint ( "saving new hiscore list to %s" % pickleFile )
        try:
            if self.backup:
                subprocess.getoutput ( "mv -f %s old_%s" % ( pickleFile, pickleFile ) )
            self.clean()
            with open( pickleFile, "wb" ) as f:
                fcntl.flock ( f, fcntl.LOCK_EX )
                pickle.dump ( self.hiscores, f )
                pickle.dump ( time.asctime(), f )
                fcntl.flock ( f, fcntl.LOCK_UN )
                f.close()
            self.mtime = os.stat ( self.pickleFile ).st_mtime
            self.fileAttempts=0
            return True
        except OSError or BlockingIOError:
            self.fileAttempts+=1
            if self.fileAttempts<5: # try again
                time.sleep ( .2 )
                self.writeListToPickle( pickleFile, check )
            return False
        return False

    def newResult ( self, protomodel ):
        """ see if new result makes it into hiscore list. If yes, then add.
        """
        if protomodel.rmax > rthresholds[0]: # we only take the ones that passed the critic
            return
        self.pprint ( "New result with K=%.2f, Z=%.2f, needs to pass K>%.2f, saving: %s" % ( protomodel.K, protomodel.Z, self.currentMinK(), "yes" if self.save_hiscores else "no" ) )
        if not self.save_hiscores:
            return
        if protomodel.K <= self.currentMinK():
            return ## clearly out
        ret = False
        ctr = 0
        while not ret:
            self.addResult ( protomodel )
            # self.log ( "now save list" )
            ret = self.save() ## and write it
            ctr+=1
            if ctr > 5:
                break
        self.log ( "done saving list" )

    def newResultByZ ( self, protomodel ):
        """ see if new result makes it into hiscore list. If yes, then add.
            Old version, going by Z, not by K.
        """
        if protomodel.rmax > rthresholds[0]: # we only take the ones that passed the critic
            return
        self.pprint ( "New result with Z=%.2f, needs to pass %.2f, saving: %s" % (protomodel.Z, self.currentMinZ(), "yes" if self.save_hiscores else "no" ) )
        if not self.save_hiscores:
            return
        if protomodel.Z <= self.currentMinZ():
            return ## clearly out
        ret = False
        ctr = 0
        while not ret:
            self.addResult ( protomodel )
            # self.log ( "now save list" )
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
    """ compile the list from individual hi*pcl
    """
    import glob
    files = glob.glob ( "H*.pcl" )
    allprotomodels=[]
    import progressbar
    pb = progressbar.ProgressBar(widgets=["file #",progressbar.Counter(),
            "/%d " % len(files), progressbar.Percentage(),
            progressbar.Bar( marker=progressbar.RotatingMarker() ),
            progressbar.AdaptiveETA()])
    pb.maxval = len(files)
    pb.start()
    for ctr,fname in enumerate(files):
        pb.update(ctr)
        try:
            with open( fname,"rb+") as f:
                #fcntl.flock( f, fcntl.LOCK_EX | fcntl.LOCK_NB )
                protomodels = pickle.load ( f )
                timestamp = "?"
                try:
                    timestamp = pickle.load(f)
                except EOFError as e:
                    pass
                #fcntl.flock( f, fcntl.LOCK_UN )
                ## add protomodels, but without the Nones
                f.close()
                allprotomodels += list ( filter ( None.__ne__, protomodels ) )
                allprotomodels = sortByK ( allprotomodels )
        except ( IOError, OSError, FileNotFoundError, EOFError, pickle.UnpicklingError ) as e:
            cmd = "rm -f %s" % fname
            print ( "[hiscore] could not open %s (%s). %s." % ( fname, e, cmd ) )
            o = subprocess.getoutput ( cmd )
    pb.finish()
    if nmax > 0:
        while len(allprotomodels)<nmax:
            allprotomodels.append ( None )
    return allprotomodels

def count ( protomodels ):
    return len(protomodels)-protomodels.count(None)

def storeList ( protomodels, savefile ):
    """ store the best protomodels in another hiscore file """
    from hiscore import Hiscore
    h = Hiscore ( 0, True, savefile, backup=True, hiscores = protomodels )
    h.hiscores = protomodels
    print ( "[hiscore] saving %d protomodels to %s" % \
            ( count(protomodels), savefile ) )
    h.writeListToPickle ( check=False )
    if "states" in savefile: ## do both for the states
        h.writeListToDictFile()

def sortByZ ( protomodels ):
    protomodels.sort ( reverse=True, key = lambda x: x.Z )
    return protomodels[:20] ## only 20

def sortByK ( protomodels ):
    protomodels.sort ( reverse=True, key = lambda x: x.K )
    return protomodels[:20] ## only 20

def discuss ( protomodel, name ):
    print ( "Currently %7s K=%.3f, Z=%.3f [%d/%d particles, %d predictions] (walker #%d)" % \
            (name, protomodel.K, protomodel.Z, len(protomodel.unFrozenParticles()),len(protomodel.masses.keys()),len(protomodel.bestCombo), protomodel.walkerid ) )

def discussBest ( protomodel, detailed ):
    """ a detailed discussion of number 1 """
    p = 2. * ( 1. - stats.norm.cdf ( protomodel.Z ) ) ## two times because one-sided
    print ( "Current      best K=%.3f, Z=%.3f, p=%.2g [%d/%d particles, %d predictions] (walker #%d)" % \
            ( protomodel.K, protomodel.Z, p, len(protomodel.unFrozenParticles()),len(protomodel.masses.keys()),len(protomodel.bestCombo), protomodel.walkerid ) )
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

def pprintEvs ( protomodel ):
    """ pretty print number of events """
    if protomodel.nevents > 1000:
        return "%dK evts" % ( protomodel.nevents/1000 )
    return str(protomodel.nevents)+ " evts"

def main ( args ):
    """ the function that updates the hiscore.pcl file
    :param args: detailed, outfile, infile, print, fetch, nmax, 
                 analysis_contributions, check, interactive, nevents.
                 see "if __main__" part below.
    :returns: { "Z": highest significance,
                "step": step, "model": model, "K": bayesian_K  }
    """

    ret =  { "Z": 0., "step": 0, "model": None, "K": -100. }

    if args.detailed:
        args.print = True
    if args.outfile.lower() in [ "none", "", "false" ]:
        args.outfile = None
    infile = args.infile
    if type(infile) is str and infile.lower() in [ "none", "" ]:
        infile = None
    rundir = setup()
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
        print ( "[hiscore] compiling list with %d protomodels" % args.nmax )
        protomodels = compileList( args.nmax ) ## compile list from H<n>.pcl files
    else:
        with open(infile,"rb") as f:
            try:
                protomodels = pickle.load ( f )
                timestamp="?"
                try:
                    timestamp = pickle.load ( f )
                except EOFError as e:
                    pass
                f.close()
            except (BlockingIOError,OSError) as e:
                print ( "file handling error on %s: %s" % ( infile, e ) )
                ## make sure we dont block!
                raise e

    if protomodels[0] == None:
        print ( "[hiscore] error, we have an empty hiscore list" )
        return ret

    triZ=-.0001
    triK=-10.

    sin = infile
    if sin == None:
        sin = "H*.pcl"
    pevs = pprintEvs ( protomodels[0] )
    print ( "[hiscore] hiscore from %s[%d] is at K=%.3f, Z=%.3f (%s)" % \
            ( sin, protomodels[0].walkerid, protomodels[0].K, protomodels[0].Z, pevs ) )

    nevents = args.nevents

    """
    if args.analysis_contributions:
        protomodel = protomodels[0]
        if not hasattr ( protomodel, "analysisContributions" ):
            from manipulator import Manipulator
            ma = Manipulator ( protomodels[0] )
            protomodel = ma.computeAnalysisContributions ()
            protomodels[0] = protomodel
    """

    if args.nmax > 0:
        protomodels = protomodels[:args.nmax]

    if args.outfile is not None:
        storeList ( protomodels, args.outfile )

    if args.check:
        protomodel = protomodels[0]
        protomodel.predict()
        print ( "[hiscore] args.check, implement" )

    if args.print:
        printProtoModels ( protomodels, args.detailed, min ( 10, args.nmax ) )

    if args.interactive:
        import manipulator
        import trimmer
        ma = manipulator.Manipulator ( protomodels[0] )
        print ( "[hiscore] starting interactive session. Variables: %sprotomodels%s" % \
                ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( "[hiscore]                                 Modules: %smanipulator, hiscore, combiner, trimmer%s" % \
                ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( "[hiscore]                          Instantiations: %sma, co, tr%s" % \
                ( colorama.Fore.RED, colorama.Fore.RESET ) )
        import combiner
        co = combiner.Combiner()
        tr = trimmer.Trimmer ( protomodels[0] )
        import hiscore
        import IPython
        IPython.embed()

    if len(protomodels)>0 and protomodels[0] != None:
        ret["Z"]=protomodels[0].Z
        ret["K"]=protomodels[0].K
        ret["step"]=protomodels[0].step
        ret["model"]=protomodels[0]
        return ret
    return ret

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore class. as a commandline tool it allows for '
                        'merging, printing, and checking of hiscore list' )
    argparser.add_argument ( '-i', '--infile',
            help='Specify the input pickle file to start with. If none, start with H<n>.pcl. [None]',
            type=str, default=None )
    argparser.add_argument ( '-o', '--outfile',
            help='pickle file with hiscores. If none, dont pickle. [none]',
            type=str, default="none" )
    argparser.add_argument ( '-n', '--nmax',
            help='maximum number of entries to store [10]',
            type=int, default=10 )
    argparser.add_argument ( '-e', '--nevents',
            help='maximum number of entries to store [50000]',
            type=int, default=50000 )
    argparser.add_argument ( '-c', '--check',
            help='check if we can reproduce Z value of first entry',
            action="store_true" )
    argparser.add_argument ( '-C', '--analysis_contributions',
            help='compute analysis contributions',
            action="store_true" )
    argparser.add_argument ( '-f', '--fetch',
            help='fetch H<n>.pcl from gpu server',
            action="store_true" )
    argparser.add_argument ( '-p', '--print',
            help='print list to stdout', action="store_true" )
    argparser.add_argument ( '-d', '--detailed',
            help='detailed descriptions (requires -p)', action="store_true" )
    argparser.add_argument ( '-I', '--interactive', help='start interactive session',
                             action="store_true" )
    args = argparser.parse_args()
    main ( args )
