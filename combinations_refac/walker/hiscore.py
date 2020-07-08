#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess, colorama
from scipy import stats
from builder.manipulator import Manipulator
from tester.combiner import  Combiner
from tools import helpers
from tools.csetup import setup

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, walkerid, save_hiscores, picklefile="hiscore.pcl",
                   backup=True, hiscores=None, predictor = None ):
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
        self.predictor = predictor
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

    def currentMinK ( self, zeroIsMin=False ):
        """ the current minimum K to make it into the list.
        :param zeroIsMin:  if false, min k can become negative
        """
        if self.hiscores[-1] == None:
            if zeroIsMin:
                return 0.
            return -30.
        mk = -10.
        if hasattr ( self.hiscores[-1], "K" ):
            mk = self.hiscores[-1].K
        if zeroIsMin:
            return max ( mk, 0. )
        return mk

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
        m = Manipulator ( protomodel )
        m.rescaleByMuHat() ## add only with resolved muhats
        if m.M.K <= self.currentMinK( zeroIsMin = True ):
            return ## doesnt pass minimum requirement
        if m.M.K == 0.:
            return ## just to be sure, should be taken care of above, though
        if m.M.K > 5.:
            ## for values > 2.5 we now predict again with larger statistics.
            self.predictor.predict (m.M)

        Kold = self.globalMaxK()
        if m.M.K > Kold:
            ## we have a new hiscore?
            ## compute the particle contributions
            if not hasattr ( m.M, "particleContributions" ):
                self.pprint ( "particleContributions missing, compute them!" )
                self.computeParticleContributions(m)
            ## compute the analysis contributions
            if not hasattr ( m.M, "analysisContributions" ):
                self.pprint ( "analysisContributions missing, compute them!" )
                self.computeAnalysisContributions(m)
            protomodel = m.M
            protomodel.getXsecs() #Make sure cross-sections have been computed

        for i,mi in enumerate(self.hiscores):
            if mi!=None and mi.almostSameAs ( m.M ):
                ### this m.M is essentially the m.M in hiscorelist.
                ### Skip!
                self.pprint ( "the protomodel seems to be already in highscore list. skip" )
                return

            if mi==None or m.M.K > mi.K: ## ok, <i>th best result!
                self.demote ( i )
                self.hiscores[i] = copy.deepcopy ( m.M )
                self.hiscores[i].cleanBestCombo( )
                break

    def computeParticleContributions ( self, manipulator ):
        """ this function sequentially removes all particles to compute
            their contributions to K """
        from smodels.tools import runtime
        runtime._experimental = True

        #Make sure the model is backep up
        manipulator.backupModel()
        protomodel = manipulator.M

        unfrozen = protomodel.unFrozenParticles( withLSP=False )
        oldZ = protomodel.Z
        oldK = protomodel.K
        protomodel.particleContributions = {} ## save the scores for the non-discarded particles.
        protomodel.particleContributionsZ = {} ## save the scores for the non-discarded particles, Zs

        #Make sure predictor is accesible
        if not self.predictor:
            self.pprint( "asked to compute particle contributions to score, but predictor has not been set")
            return

        ## aka: what would happen to the score if I removed particle X?
        frozen = protomodel.frozenParticles()

        for pid in frozen:
            ## remove ssmultipliers for frozen particles
            if pid in protomodel.ssmultipliers:
                protomodel.ssmultipliers.pop(pid)
            protomodel.masses[pid]=1e6 ## renormalize


        pidsnmasses = [ (x,protomodel.masses[x]) for x in unfrozen ]
        pidsnmasses.sort ( key=lambda x: x[1], reverse=True )
        for cpid,(pid,mass) in enumerate(pidsnmasses):
            protomodel.highlight ( "info", "computing contribution of %s (%.1f): [%d/%d]" % \
                   ( helpers.getParticleName(pid,addSign=False),
                     protomodel.masses[pid],(cpid+1),len(unfrozen) ) )

            #Remove particle and recompute SLHA file:
            manipulator.freezeParticle(pid)
            protomodel.createSLHAFile()
            self.predictor.predict( protomodel )
            percK = 0.
            if oldK > 0.:
                percK = ( protomodel.K - oldK ) / oldK
            self.pprint ( "when removing %s, K changed: %.3f -> %.3f (%.1f%s), Z: %.3f -> %.3f (%d evts)" % \
                    ( helpers.getParticleName(pid), oldK, protomodel.K, 100.*percK, "%", oldZ,protomodel.Z, protomodel.nevents ) )

            #Store the new Z and K values in the original model:
            protomodel.particleContributions[pid]=manipulator.M.K
            protomodel.particleContributionsZ[pid]=manipulator.M.Z
            #Make sure to restore the model to its initial (full particle content) state
            manipulator.restoreModel()

        self.pprint ( "stored %d particl contributions" % len(protomodel.particleContributions) )

    def computeAnalysisContributions( self, manipulator ):
        """ compute the contributions to Z of the individual analyses
        :returns: the model with the analysic constributions attached as
                  .analysisContributions
        """

        #Make sure the protomodel is backed up
        manipulator.backupModel()
        protomodel = manipulator.M
        self.pprint ( "Now computing analysis contributions" )
        self.pprint ( "step 1: Recompute the score. Old one at K=%.2f, Z=%.2f" % \
                      ( protomodel.K, protomodel.Z ) )
        protomodel.createNewSLHAFileName ( prefix="acc" )
        contributionsZ = {}
        contributionsK = {}
        combiner = Combiner()
        dZtot, dKtot = 0., 0.
        bestCombo = copy.deepcopy ( protomodel.bestCombo )
        for ctr,pred in enumerate(bestCombo):
            combo = copy.deepcopy ( bestCombo )[:ctr]+copy.deepcopy ( bestCombo)[ctr+1:]
            Z, muhat_ = combiner.getSignificance ( combo )
            prior = combiner.computePrior ( protomodel )
            K = combiner.computeK ( Z, prior )
            dZ = protomodel.Z - Z
            dK = protomodel.K - K
            dZtot += dZ
            dKtot += dK
            contributionsZ[ ctr ] = Z
            contributionsK [ ctr ] = K
        for k,v in contributionsZ.items():
            percZ = (protomodel.Z-v) / dZtot
            self.pprint ( "without %s(%s) we get Z=%.3f (%d%s)" % ( protomodel.bestCombo[k].analysisId(), protomodel.bestCombo[k].dataType(short=True), v, 100.*percZ,"%" ) )
            contributionsZ[ k ] = percZ
        for k,v in contributionsK.items():
            percK = (protomodel.K-v) / dKtot
            # self.pprint ( "without %s(%s) we get Z=%.3f (%d%s)" % ( self.M.bestCombo[k].analysisId(), self.M.bestCombo[k].dataType(short=True), v, 100.*perc,"%" ) )
            contributionsK[ k ] = percK
        contrsWithNames = {}
        for k,v in contributionsZ.items():
            contrsWithNames [ protomodel.bestCombo[k].analysisId() ] = v
        protomodel.analysisContributions = contrsWithNames
        self.pprint ( "stored %d analyses contributions" % len(protomodel.analysisContributions) )

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
                    except EOFError:
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
                m=Manipulator ( h )
                m.rescaleByMuHat()
                m.delBackup ( )
                m.M.cleanBestCombo ()
                self.hiscores[ctr+1]=m.M

    def save ( self ):
        """ later will do something smarter """
        self.writeListToPickle()

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
        if len ( self.hiscores ) == 0:
            self.log ( "hiscore list is empty will not write out" )
            return
        onlyNones = True
        for i in self.hiscores:
            if i != None:
                onlyNones = False
                break
        if onlyNones:
            self.log ( "hiscore list contains only nones" )
            return
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
            # self.clean()
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
        if protomodel.excluded: # we only take the ones that passed the critic
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
        if protomodel.excluded: # we only take the ones that passed the critic
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
