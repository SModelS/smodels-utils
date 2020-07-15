#!/usr/bin/env python3

""" Class that takes care of xsec computations of protomodels """

from smodels.tools.xsecComputer import XSecComputer, LO, NLL
import pyslha, time, subprocess

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

    def hasPID ( self, pid, frozen_counts=False ):
        """ check if a certain PID appears in the file
        :param frozen_counts: it also counts if the particle is in fact frozen
        """
        f = pyslha.readSLHAFile ( self.slhafile )
        m = f.blocks["MASS"]
        pid=abs(pid)
        if not pid in m:
            return False
        if frozen_counts:
            return True
        if m[pid]<8e4:
            return True
        return False

    def backup ( self ):
        """ backup the current SLHA file """
        self.backupfile = self.slhafile.replace(".slha",".bu.slha")
        cmd = "cp %s %s" % ( self.slhafile, self.backupfile )
        o = subprocess.getoutput ( cmd )

    def restore ( self ):
        """ restore the SLHA file from the backup """
        if self.backupfile == None:
            self.pprint ( "was asked to restore SLHA file but no backup exists" )
            return
        cmd = "cp %s %s" % ( self.backupfile, self.slhafile )
        o = subprocess.getoutput ( cmd )

    def __init__ ( self, walkerid, nevents, slhafile, ssmultipliers, step ):
        self.walkerid = walkerid
        self.backupfile = None
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
            self.pprint ( "Could not compute xsecs %s: %s" % ( self.slhafile, e ) )
            self.pprint ( "pythia version is %s" % self.computer.getPythia().srcPath )
            # self.pprint ( "lets restore old state" )
            raise e


if __name__ == "__main__":
    import subprocess
    subprocess.getoutput ( "cp empty.slha test.slha" )
    ssms = { (1000002, 1000002):0.1841, (-1000002, 1000002):0.1841, (1000002, 1000003):0.8651, (-1000003, 1000002):0.8651, (1000002, 1000021):0.09084, (1000002, 1000022):0.4196, (-1000002, -1000002):0.1841, (-1000002, 1000003):0.8651, (-1000003, -1000002):0.8651, (-1000002, 1000021):0.09084, (-1000002, 1000022):0.4196, (-1000006, 1000006):0.299, (-2000006, 1000006):0.359, (-1000006, 2000006):0.359, (-2000006, 2000006):0.346, (1000021, 1000021):0.064, (1000021, 1000022):0.217 }
    p = ProtoModelXSecs( 0, 10000, "test.slha", ssms, step=1 )
    print ( "has 1000021", p.hasPID ( 1000021 ) )
    print ( "has 2000021", p.hasPID ( 2000021 ) )
    D = p.compute()
    # print ( D )
