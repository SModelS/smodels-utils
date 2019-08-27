#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess
from trimmer import Trimmer

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, walkerid, save_hiscores, picklefile="hiscore.pcl" ):
        self.walkerid = walkerid
        self.trimmed = {}
        self.save_hiscores = save_hiscores
        self.nkeep = 3 ## how many do we keep.
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
                if False and i == 0 and model.Z > 3.0: ## awesome new hiscore? trim it!
                    self.trimModels(1,True)
                break
            
    def demote ( self, i ):
        """ demote everything from i+1 on, 
            i.e (i+1)->(i+2), (i+2)->(i+3) and so on """
        for j in range(self.nkeep-1,i,-1):
            m = copy.deepcopy ( self.hiscores[j-1] )
            self.hiscores[j]= m
            if (j-1) in self.trimmed.keys():
                self.trimmed[j] = copy.deepcopy ( self.trimmed[j-1] )
                self.trimmed[j].clean( all=True ) # just in case
            else:
                if j in self.trimmed:
                    self.trimmed.pop(j)
        if len(self.hiscores)>self.nkeep:
            self.hiscores = self.hiscores[:self.nkeep]
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
            nhs = 0
            for i in self.hiscores:
                if i != None:
                    nhs += 1
            self.pprint ( "loaded %d hiscores from file, and %s trimmed ones." % ( nhs,len(self.trimmed) ) )
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
