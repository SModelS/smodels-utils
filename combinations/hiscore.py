#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, walkerid, save_hiscores ):
        self.walkerid = walkerid
        self.save_hiscores = save_hiscores
        self.nkeep = 20 ## how many do we keep.
        self.hiscores = {}
        self.fileAttempts = 0 ## unsucessful attempts at reading or writing
        self.pickleFile = "hiscore.pcl"
        self.updateListFromPickle ( )

    def currentMinZ ( self ):
        """ the current minimum Z to make it into the list. """
        if len(self.hiscores)==0:
            return 0.
        return min ( self.hiscores.keys() )

    def addResult ( self, model ):
        """ add a result to the list """
        while model.Z in self.hiscores.keys():
            model.Z = model.Z-1e-20
        self.hiscores[model.Z]=copy.deepcopy(model)
        self.trimList()

    def trimList ( self ):
        keys = list ( self.hiscores.keys() )
        if len(keys)<= self.nkeep:
            return
        keys.sort( reverse=True )
        tmp = {}
        for k in keys[:self.nkeep]:
            tmp[k]=copy.deepcopy ( self.hiscores[k] )
        self.hiscores = tmp

    def updateListFromPickle ( self ):
        """ fetch the list from the pickle file """
        if not os.path.exists ( self.pickleFile ) or os.stat ( self.pickleFile ).st_size < 100:
            return
        try:
            f=open( self.pickleFile,"rb")
            oldhiscores = copy.deepcopy ( self.hiscores )
            self.hiscores = pickle.load ( f )
            self.pprint ( "loaded %d hiscores from file." % ( len(self.hiscores.keys()) ) )
            f.close()
            self.fileAttempts=0
        except OSError or BlockingIOError or EOFError or pickle.UnpicklingError as e:
            self.fileAttempts+=1
            if self.fileAttempts<10: # try again
                self.pprint ( "Waiting for %s file" % self.pickleFile )
                time.sleep ( (.2 + random.uniform(0.,.1))*self.fileAttempts )
                self.updateListFromPickle()
            else:
                raise(e)

    def writeListToPickle ( self ):
        """ dump the list to the pickle file """
        self.pprint ( "saving new hiscore list." )
        try:
            subprocess.getoutput ( "cp %s old.pcl" % self.pickleFile )
            f=open( self.pickleFile,"wb" )
            fcntl.lockf( f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            pickle.dump ( self.hiscores, f )
            fcntl.lockf( f, fcntl.LOCK_UN )
            f.close()
            self.fileAttempts=0
        except OSError or BlockingIOError:
            self.fileAttempts+=1
            if self.fileAttempts<5: # try again
                time.sleep ( .2 )
                self.writeListToPickle()

    def newResult ( self, model ):
        """ see if new result makes it into hiscore list. If yes, then add.
        """
        # self.pprint ( "New result with Z=%.2f, %s" % (model.Z, self.save_hiscores ) )
        if not self.save_hiscores:
            return
        if model.Z <= 0.: ## we ignore models with Z==0.
            return
        if len ( self.hiscores.keys() ) > 0 and \
            model.Z < self.currentMinZ():
                return ## clearly out
        self.updateListFromPickle() ## load the current version again
        self.addResult ( model )
        self.writeListToPickle() ## and write it

    def pprint ( self, *args ):
        """ logging """
        print ( "[hiscore:%d] %s" % ( self.walkerid, " ".join(map(str,args))) )
