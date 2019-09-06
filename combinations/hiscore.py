#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess, colorama
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

    def addResult ( self, model ):
        """ add a result to the list """
        if model.Z <= self.currentMinZ():
            return ## doesnt pass minimum requirement
        for i,mi in enumerate(self.hiscores):
            if mi==None or model.Z > mi.Z: ## ok, <i>th best result!
                self.demote ( i )
                self.hiscores[i] = copy.deepcopy ( model )
                self.hiscores[i].clean( all=True )
                self.trimmed[i] = None
                break

    def demote ( self, i ):
        """ demote everything from i+1 on,
            i.e (i+1)->(i+2), (i+2)->(i+3) and so on """
        for j in range(self.nkeep-1,i,-1):
            m = copy.deepcopy ( self.hiscores[j-1] )
            self.hiscores[j]= m
            while len(self.trimmed)=<j:
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

    def trimModels ( self, n=None, trimbranchings=False, maxloss=.01 ):
        """ trim the first <n> models in the list """
        if n == None or n < 0 or n > self.nkeep:
            n = self.nkeep
        for i in range(n):
            if self.hiscores[i]!=None:
                trimmer = Trimmer( self.hiscores[i], "aggressive", maxloss )
                trimmer.trim( trimbranchings=trimbranchings )
                while len(self.trimmed)<=i:
                    self.trimmed.append ( None )
                self.trimmed[i] = trimmer.model

    def clean ( self ):
        """ clean hiscore list, i.e. remove cruft from models.
            leave first one as it is """
        for h in self.hiscores[1:]:
            if h != None:
                h.clean( all=True )

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

    def newResult ( self, model ):
        """ see if new result makes it into hiscore list. If yes, then add.
        """
        # self.pprint ( "New result with Z=%.2f, %s" % (model.Z, self.save_hiscores ) )
        self.log("lets see if it is above threshold" )
        if not self.save_hiscores:
            return
        if model.Z <= self.currentMinZ():
            return ## clearly out
        ret = False
        ctr = 0
        while not ret:
            self.addResult ( model )
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
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[hiscore:%d - %s] %s\n" % ( self.walkerid, time.asctime(), " ".join(map(str,args)) ) )

def compileList():
    """ compile the list from individual hi*pcl """
    import glob
    files = glob.glob ( "H*.pcl" )
    allmodels,alltrimmed=[],[]
    for f in files:
        try:
            with open( f,"rb+") as f:
                fcntl.flock( f, fcntl.LOCK_EX )
                models = pickle.load ( f )
                trimmed = pickle.load ( f )
                fcntl.flock( f, fcntl.LOCK_UN )
                ## add models, but without the Nones
                allmodels += list ( filter ( None.__ne__, models ) )
                alltrimmed += list ( filter ( None.__ne__, trimmed ) )
        except:
            print ( "could not open %s. ignore." % f.name )
    allmodels = sortByZ ( allmodels )
    alltrimmed = sortByZ ( alltrimmed )
    return allmodels, alltrimmed

def storeList ( models, trimmed, savefile ):
    """ store the best models in another hiscore file """
    from hiscore import Hiscore
    h = Hiscore ( 0, True, savefile )
    h.hiscores = models
    h.trimmed = trimmed
    h.save()

def sortByZ ( models ):
    models.sort ( reverse=True, key = lambda x: x.Z )
    return models

def discuss ( model, name ):
    print ( "Currently %7s Z is: %.3f [%d/%d unfrozen particles, %d predictions] (walker #%d)" % \
            (name, model.Z, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo), model.walkerid ) )

def discussBest ( model, detailed ):
    """ a detailed discussion of number 1 """
    p = 1. - stats.norm.cdf ( model.Z )
    print ( "Current           best: %.3f, p=%.2g [%d/%d unfrozen particles, %d predictions] (walker #%d)" % \
            (model.Z, p, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo), model.walkerid ) )
    if detailed:
        print ( "Solution was found in step #%d" % model.step )
        for i in model.bestCombo:
            print ( "  prediction in best combo: %s (%s)" % ( i.analysisId(), i.dataType() ) )

def printModels ( models, detailed ):
    names = { 0: "highest", 1: "second", 2: "third" }
    for c,model in enumerate(models):
        if c >= args.nmax:
            break
        if model == None:
            break
        sc = "%dth" % (c+1)
        if c in names.keys():
            sc = names[c]
        if c==0:
            discussBest ( model, detailed )
        else:
            discuss ( model, sc )

def produceNewSLHAFileNames ( models ):
    for m in models:
        m.createNewSLHAFileName()

def main ( args ):
    if args.detailed:
        args.print = True
    if args.outfile.lower() in [ "none", "", "false" ]:
        args.outfile = None
    if type(args.infile) is str and args.infile.lower() in [ "none", "" ]:
        args.infile = None

    if args.fetch:
        import subprocess
        cmd = "scp gpu:/local/wwaltenberger/git/smodels-utils/combinations/H*.pcl ."
        out = subprocess.getoutput ( cmd )
        print ( out )

    if args.infile is None:
        models,trimmed = compileList() ## compile list from H<n>.pcl files
    else:
        with open(args.infile,"rb+") as f:
            fcntl.flock( f, fcntl.LOCK_EX )
            models = pickle.load ( f )
            trimmed = pickle.load ( f )
            fcntl.flock( f, fcntl.LOCK_UN )

    produceNewSLHAFileNames ( models )
    produceNewSLHAFileNames ( trimmed )

    if args.trim:
        model = models[0]
        tr = Trimmer ( model )
        tr.trimParticles()
        trimmed[0] = tr.model

    if args.trim_branchings:
        if 0 in trimmed:
            ## already has a trimmed model? trim only branchings
            model = trimmed[0]
            tr = Trimmer ( model )
            tr.trimBranchings()
            trimmed[0] = tr.model
        else:
            model = models[0]
            tr = Trimmer ( model )
            tr.trimParticles()
            tr.trimBranchings()
            trimmed[0] = tr.model

    if args.analysis_contributions:
        model = models[0]
        if 0 in trimmed:
            model = trimmed[0]
        tr = Trimmer ( model )
        model = tr.computeAnalysisContributions ()
        if 0 in trimmed:
            trimmed[0] = model
        else:
            models[0] = model

    if args.nmax > 0:
        models = models[:args.nmax]
        trimmed = trimmed[:args.nmax]

    if args.outfile is not None:
        storeList ( models, trimmed, args.outfile )

    if args.check:
        model = models[0]
        if len(trimmed)>0:
            model = trimmed[0]
        tr = Trimmer ( model )
        tr.checkZ()

    if args.print:
        printModels ( models, args.detailed )

    if args.interactive:
        print ( "[hiscore] starting interactive session. Variables: %smodels, trimmed%s" % \
                ( colorama.Fore.RED, colorama.Fore.RESET ) )
        import IPython
        IPython.embed()

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
            help='trim leading model, but only particles', action="store_true" )
    argparser.add_argument ( '-T', '--trim_branchings',
            help='trim leading model, also branchings',
            action="store_true" )
    argparser.add_argument ( '-p', '--print',
            help='print list to stdout', action="store_true" )
    argparser.add_argument ( '-d', '--detailed',
            help='detailed descriptions (requires -p)', action="store_true" )
    argparser.add_argument ( '-I', '--interactive', help='start interactive session',
                             action="store_true" )
    args = argparser.parse_args()

    main ( args )
