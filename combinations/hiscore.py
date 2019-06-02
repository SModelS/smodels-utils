#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess
from trimmer import Trimmer

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, walkerid, save_hiscores, picklefile="hiscore.pcl" ):
        self.walkerid = walkerid
        self.save_hiscores = save_hiscores
        self.nkeep = 20 ## how many do we keep.
        self.hiscores = [ None ]*self.nkeep
        self.fileAttempts = 0 ## unsucessful attempts at reading or writing
        self.pickleFile = picklefile
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
                break
            
    def demote ( self, i ):
        """ demote everything from i+1 on, 
            i.e (i+1)->(i+2), (i+2)->(i+3) and so on """
        for j in range(self.nkeep-1,i,-1):
            m = copy.deepcopy ( self.hiscores[j-1] )
            self.hiscores[j]= m
        assert ( len(self.hiscores) == self.nkeep )

    def updateListFromPickle ( self ):
        """ fetch the list from the pickle file """
        if not os.path.exists ( self.pickleFile ) or os.stat ( self.pickleFile ).st_size < 100:
            return
        try:
            f=open( self.pickleFile,"rb")
            self.hiscores = pickle.load ( f )
            self.pprint ( "loaded %d hiscores from file." % ( len(self.hiscores) ) )
            f.close()
            assert ( len(self.hiscores) == self.nkeep )
            self.fileAttempts=0
        except Exception as e:
        # except OSError or BlockingIOError or EOFError or pickle.UnpicklingError or TypeError as e:
            self.fileAttempts+=1
            if self.fileAttempts<20: # try again
                self.pprint ( "Exception %s: Waiting for %s file, %d" % (str(e),self.pickleFile,self.fileAttempts) )
                time.sleep ( (.2 + random.uniform(0.,1.))*self.fileAttempts )
                self.updateListFromPickle()
            else:
                self.pprint ( "Timed out when try to get hiscores!" )

    def trimModels ( self, n=None ):
        """ trim the first <n> models in the list """
        if n == None or n < 0 or n > self.nkeep:
            n = self.nkeep
        for i in range(n):
            if self.hiscores[i]!=None:
                trimmer = Trimmer( self.hiscores[i], "aggressive", .002 )
                trimmer.trim( trimbranchings=False )
                self.hiscores[i] = trimmer.model

    def clean ( self ):
        """ clean hiscore list, i.e. remove cruft from models """
        for h in self.hiscores:
            if h != None:
                h.clean()

    def writeListToPickle ( self, pickleFile=None ):
        """ dump the list to the pickle file <pickleFile>.
            If pickleFile is None, then self.pickleFile is used.
        """
        if pickleFile==None:
            pickleFile = self.pickleFile
        self.pprint ( "saving new hiscore list to %s" % pickleFile )
        try:
            subprocess.getoutput ( "mv -f %s old.pcl" % pickleFile )
            self.clean()
            f=open( pickleFile, "wb" )
            fcntl.lockf( f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            pickle.dump ( self.hiscores, f )
            fcntl.lockf( f, fcntl.LOCK_UN )
            f.close()
            self.fileAttempts=0
        except OSError or BlockingIOError:
            self.fileAttempts+=1
            if self.fileAttempts<5: # try again
                time.sleep ( .2 )
                self.writeListToPickle( pickleFile )

    def newResult ( self, model ):
        """ see if new result makes it into hiscore list. If yes, then add.
        """
        # self.pprint ( "New result with Z=%.2f, %s" % (model.Z, self.save_hiscores ) )
        if not self.save_hiscores:
            return
        if model.Z <= self.currentMinZ():
            return ## clearly out
        self.updateListFromPickle() ## reload the hiscores 
        self.addResult ( model )
        self.writeListToPickle() ## and write it

    def pprint ( self, *args ):
        """ logging """
        print ( "[hiscore:%d] %s" % ( self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        f=open( "walker%d.log" % self.walkerid, "a" )
        f.write ( "[hiscore:%d - %s] %s\n" % ( self.walkerid, time.asctime(), " ".join(map(str,args)) ) )
        f.close()
