#!/usr/bin/env python3

""" A class that stores the history of a random walk """

import pickle

class History:
    """ encapsulates the history of one random walk """
    def __init__ ( self, walkerid ):
        self.walkerid = walkerid
        self.history = []

    def add ( self, model ):
        """ keep masses, signal strength multipliers, decays """
        self.history.append ( { "masses": model.masses, "ssmultipliers": model.ssmultipliers, "decays": model.decays, "step": model.step } )
        if len(self.history) == 3:
            self.save()
        if len(self.history) == 10:
            self.save()
        if len(self.history) % 100 == 0:
            self.save()

    def pprint ( self, *args ):
        """ logging """
        print ( "[history:%d] %s" % ( self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[history:%d - %s] %s\n" % ( self.walkerid, time.asctime(), " ".join(map(str,args)) ) )

    def save ( self ):
        self.pprint ( "saving history" )
        with open("history.pcl","wb") as f:
            pickle.dump(self.history,f)

    def load ( self ):
        f=open("history.pcl","rb" )
        self.history = pickle.load(f)
        f.close()

