#!/usr/bin/env python3

""" Class that takes care of xsec computations of protomodels """

from smodels.tools.xsecComputer import XSecComputer, LO, NLL
import pyslha
import time

class ProtoModelXSecs:
    """ codes that takes care of the cross section computations
        for protomodels. Takes care of the exotic particles,
        signal strength multipliers, etc.
    """

    def pprint ( self, *args ):
        """ logging """
        print ( "[model:%d] %s" % (self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[model:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def __init__ ( self, walkerid, nevents, slhafile, ssmultipliers, step ):
        self.walkerid = walkerid
        self.computer = XSecComputer ( NLL, nevents, 8 )
        self.nevents = nevents
        self.computer.countNoNLOXSecs = 4
        self.slhafile = slhafile
        self.ssmultipliers = ssmultipliers
        self.step = step
        self.log ( "computing xsecs with %d events" % nevents )

    def addInfoToFile ( self, stored_xsecs ):
        ## add the cahced info and the ssmutlipliers to SLHA file
        self.computer.addXSecToFile( stored_xsecs[0], self.slhafile, "recycled" )
        self.computer.addMultipliersToFile ( self.ssmultipliers, self.slhafile )
        self.computer.addCommentToFile ( stored_xsecs[1], self.slhafile )

    def checkIfReadable ( self ):
        """ check if SLHA file is readable """
        try:
            f = pyslha.readSLHAFile ( self.slhafile )
            m = f.blocks["MASS"]
        except Exception as e:
            self.pprint ( "could not read SLHA file %s: %s" % ( self.slhafile, e ) )
            self.pprint ( "lets restore old state" )
            raise e
                

    def compute ( self ):
        """ compute xsecs for self.slhafile
        :param step: the step at which it was produced, for the comment
        :returns: list with cross sections, comment
        """
        try:
            comment = "produced at step %d" % ( self.step )
            tofile = "all"

            xsecs, nXsecs = [], 0
            for sqrts in [8, 13]:
                nXsecs += self.computer.computeForOneFile ( [sqrts], self.slhafile,
                        unlink=True, lOfromSLHA=False, tofile=tofile,
                        ssmultipliers  = self.ssmultipliers, comment = comment )
                for x in self.computer.loXsecs:
                    xsecs.append ( x )
                for x in self.computer.xsecs:
                    xsecs.append ( x )

            self.log ( "done computing %d xsecs" % nXsecs )
            return xsecs, comment
        except Exception as e:
            self.pprint ( "could not compute xsecs %s: %s" % ( self.slhafile, e ) )
            self.pprint ( "lets restore old state" )
            raise e


if __name__ == "__main__":
    p = ProtoModelXSecs( 0, 10000, "bla.slha", {}, 1 )
