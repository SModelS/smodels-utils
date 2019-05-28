#!/usr/bin/env python3

""" A class that centralizes access to the hiscore list over multiple threads.
"""

import random, copy, pickle, os, fcntl, time, subprocess

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, walkerid, save_hiscores, picklefile="hiscore.pcl" ):
        self.walkerid = walkerid
        self.save_hiscores = save_hiscores
        self.nkeep = 20 ## how many do we keep.
        self.hiscores = {}
        self.fileAttempts = 0 ## unsucessful attempts at reading or writing
        self.pickleFile = picklefile
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
        """ trim the list down to <nkeep> entries. """
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
            # oldhiscores = copy.deepcopy ( self.hiscores )
            self.hiscores = pickle.load ( f )
            self.pprint ( "loaded %d hiscores from file." % ( len(self.hiscores.keys()) ) )
            f.close()
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
        if n == None:
            n = len(self.hiscores)
        if n < 0:
            n = len(self.hiscores)
        if n > len(self.hiscores):
            n = len(self.hiscores)
        for i in range(n):
            self.getModelNr(i).trim()

    def getModelNr ( self, nr ):
        """ get the nth model in the hiscore list """
        if nr < 0 or nr >= self.nkeep:
            self.pprint ( "asking for model nr %d: does not exist." % nr )
            return None
        keys = list ( self.hiscores.keys() )
        keys.sort ( reverse=True )
        return self.hiscores[keys[nr]]

    def writeListToPickle ( self, pickleFile=None ):
        """ dump the list to the pickle file <pickleFile>.
            If pickleFile is None, then self.pickleFile is used.
        """
        if pickleFile==None:
            pickleFile = self.pickleFile
        self.pprint ( "saving new hiscore list to %s" % pickleFile )
        try:
            subprocess.getoutput ( "mv -f %s old.pcl" % pickleFile )
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
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        f=open( "walker%d.log" % self.walkerid, "a" )
        f.write ( "[hiscore:%d - %s] %s\n" % ( self.walkerid, time.asctime(), " ".join(map(str,args)) ) )
        f.close()
