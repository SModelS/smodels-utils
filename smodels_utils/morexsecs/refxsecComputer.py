#!/usr/bin/env python3

"""
.. module:: refxsecComputer
   :synopsis: code to retrieve cross sections from LHC Xsec group's
              references, published at
              https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function
from smodels.tools.wrapperBase import WrapperBase
from smodels.tools import wrapperBase
from smodels.tools.smodelsLogging import logger, setLogLevel
from smodels.tools.physicsUnits import fb, pb, GeV, TeV, mb, unum
from smodels.theory.crossSection import LO, NLO, NLL, NNLL
from smodels.theory import crossSection
from smodels_utils.SModelSUtils import installDirectory
from smodels.theory.exceptions import SModelSTheoryError as SModelSError
from smodels import installation as smodelsinstallation
import os, sys, io, shutil, pyslha

class RefXSecComputer:
    """
    The xsec computer that simply looks up reference cross sections,
    and interpolates them.
    """
    version = "1.0" ## make sure we can trace changes in the tables

    def __init__( self, verbose = False ):
        """
        :param verbose: turn on verbose mode, for debugging 
        """
        self.verbose = verbose
        if verbose:
            setLogLevel ( "info" )
        self.shareDir = os.path.join ( installDirectory(), "smodels_utils", \
                                       "morexsecs", "tables" )

    def checkFileExists(self, inputFile):
        """
        Check if file exists, raise an IOError if it does not.
        :returns: absolute file name if file exists.

        """
        nFile = self.absPath(inputFile)
        if not os.path.exists(nFile):
            raise IOError("file %s does not exist" % nFile)
        return nFile

    def dictToXSection ( self, D ):
        """ create an XSection object from dictionary D """
        xsec = crossSection.XSection()
        xsec.value = D["xsec"]*pb
        xsec._pid = D["pids"]
        xsec.info = crossSection.XSectionInfo ( D["sqrts"]*TeV, D["order"], D["label"] )
        return xsec

    def addXSecToFile( self, xsecs, slhafile, complain=True):
        """
        Write cross sections to an SLHA file, analogous to xsecComputer

        :param xsecs: a XSectionList object containing the cross sections
        :param slhafile: target file for writing the cross sections in SLHA format
        :param complain: complain if there are already cross sections in file

        """

        if not os.path.isfile(slhafile):
            line = f"SLHA file {slhafile} not found."
            logger.error( line )
            raise SModelSError( line )
        if len(xsecs) == 0:
            logger.warning(f"No cross sections available for {slhafile}.")
            return False
        print ( "I have xsecs!!", xsecs )
        # Check if file already contain cross section blocks
        xSectionList = crossSection.getXsecFromSLHAFile(slhafile)
        if xSectionList and complain:
            logger.info("SLHA file already contains XSECTION blocks. Adding "
                           "only missing cross sections.")

        # Write cross sections to file, if they do not overlap any cross section in
        # the file
        outfile = open(slhafile, 'a')
        nxsecs = 0
        for xsec in xsecs:
            xseccomment = f"reference xsecs v{self.version} [pb]"
            writeXsec = True
            for oldxsec in xSectionList:
                if oldxsec.info == xsec.info and set(oldxsec.pid) == set(xsec.pid):
                    writeXsec = False
                    break
            if writeXsec:
                nxsecs += 1
                outfile.write( self.xsecToBlock(xsec, (2212, 2212), xseccomment) + "\n")
        outfile.close()

        return nxsecs

    def xsecToBlock( self, xsec, inPDGs=(2212, 2212), comment=None, xsecUnit = pb):
        """
        Generate a string for a XSECTION block in the SLHA format from a XSection
        object.

        :param inPDGs: defines the PDGs of the incoming states
                       (default = 2212,2212)

        :param comment: is added at the end of the header as a comment
        :param xsecUnit: unit of cross sections to be written (default is pb).
                         Must be a Unum unit.

        """
        if type(xsec) != type(crossSection.XSection()):
            logger.error("Wrong input")
            raise SModelSError()
        # Sqrt(s) in GeV
        header = "XSECTION  " + str(xsec.info.sqrts / GeV)
        for pdg in inPDGs:
            # PDGs of incoming states
            header += " " + str(pdg)
        # Number of outgoing states
        header += " " + str(len(xsec.pid))
        for pid in xsec.pid:
            # PDGs of outgoing states
            header += " " + str(pid)
        if comment:
            header += " # " + str(comment)  # Comment
        entry = "  0  " + str(xsec.info.order) + "  0  0  0  0  " + \
                str( "%16.8E" % (xsec.value / xsecUnit) ) + " SModelSv" + \
                     smodelsinstallation.version()

        return "\n" + header + "\n" + entry

    def computeForOneFile ( self, sqrtses, inputFile,
                            tofile, ssmultipliers = None, comment = None ):
        """
        Compute the cross sections for one file.

        :param sqrtses: list of sqrt{s} tu run pythia, as a unum (e.g. [7*TeV])
        :param inputFile: input SLHA file to compute xsecs for
        :param tofile: False, True, "all": write results to file,
                       if "all" also write lower xsecs to file.
        :param ssmultipliers: optionally supply signal strengh multipliers,
                          given as dictionary of the tuple of the mothers' pids as keys and
                          multipliers as values, e.g { (1000001,1000021):1.1 }.
        :param comment: an optional comment that gets added to the slha file.

        :returns: number of xsections that have been computed
        """
        self.xsecs = crossSection.XSectionList()
        nXSecs = 0
        if tofile:
            logger.info("Computing SLHA cross section from %s, adding to "
                        "SLHA file." % inputFile )
            complain = True ## dont complain about already existing xsecs,
            # if we were the ones writing them
            for s in sqrtses:
                # ss = s*TeV
                self.compute( s, inputFile, ssmultipliers = ssmultipliers )
                if tofile == "all" and hasattr ( self, "loXSecs" ):
                    nXSecs += self.addXSecToFile(self.loXsecs, inputFile, complain )
                    complain = False
                if tofile != False:
                    ## FIXME check if higher orders are already in from
                    ## ref xsecs
                    nXSecs += self.addXSecToFile( self.xsecs, inputFile, complain)
                    complain = False
            if nXSecs > 0: ## only add if we actually added xsecs
                self.addMultipliersToFile ( ssmultipliers, inputFile )
            self.addCommentToFile ( comment, inputFile )
            self.cleanSLHAFile ( inputFile )
        else:
            logger.info("Computing SLHA cross section from %s." % inputFile )
            print()
            print( "     Cross sections:" )
            print( "=======================" )
            for s in sqrtses:
                ss = s*TeV
                self.compute( ss, inputFile, unlink=unlink, loFromSlha=lOfromSLHA,
                              ssmultipliers = ssmultipliers )
                for xsec in self.xsecs:
                    nXSecs += 1
                    print( "%s %20s:  %.3e pb" % \
                            ( xsec.info.label,xsec.pid,xsec.value/pb ) )
            print()
        return nXSecs

    def cleanSLHAFile ( self, slhafile ):
        """ clean up F, if needed. remove double newlines """
        f=open(slhafile,"rt")
        lines=f.readlines()
        f.close()
        f=open(slhafile,"wt")
        newline = False
        for line in lines:
            #if "Signal strength multipliers" in line:
            #    continue
            if newline and line == "\n":
                continue
            if line == "\n":
                newline = True
            else:
                newline = False
            f.write ( line )
        f.close()

    def computeForBunch ( self, sqrtses, inputFiles, tofile, ssmultipliers=None ):
        """ compute xsecs for a bunch of slha files """
        for inputFile in inputFiles:
            logger.debug ( "computing xsec for %s" % inputFile )
            self.computeForOneFile ( sqrtses, inputFile, tofile, 
                                     ssmultipliers = ssmultipliers )

    def addCommentToFile ( self, comment, slhaFile ):
        """ add the optional comment to file """
        if comment in [ None, "" ]:
            return
        if not os.path.isfile(slhaFile ):
            logger.error("SLHA file %s not found." % slhaFile )
            raise SModelSError()
        outfile = open(slhaFile, 'a')
        outfile.write ( "# %s\n" % comment )
        outfile.close()

    def addMultipliersToFile ( self, ssmultipliers, slhaFile ):
        """ add the signal strength multipliers to the SLHA file """
        if ssmultipliers in [ None, {} ]:
            return
        if not os.path.isfile(slhaFile ):
            logger.error("SLHA file %s not found." % slhaFile )
            raise SModelSError()
        tokens = []
        for k,v in ssmultipliers.items():
            tokens.append ( "%s:%.4g" % ( k, v ) )
        newline = "# Signal strength multipliers: " + ", ".join ( tokens )
        with open(slhaFile, 'r' ) as r:
            lines = r.readlines()
            r.close()

        rewrite = []
        for line in lines:
            if "Signal strength multipliers" in line:
                if ( line.strip() == newline ):
                    logger.debug ( "Signal strength multipliers have alread been applied." )
                else:
                    logger.error ( "Different signal strength multipliers have alread been applied!!!" )
                    rewrite.append ( line+" ERROR inconsistent!" )
            else:
                if not "produced at step" in line:
                    rewrite.append ( line )
        outfile = open(slhaFile, 'w')
        for line in rewrite:
            outfile.write ( line )
        if line != "\n": ## last line not an empty newline?
            outfile.write ( "\n" )
        outfile.write ( newline )
        outfile.write ( "\n" )
        outfile.close()

    def compute( self, sqrts, slhafile, ssmultipliers = None ):
        """
        Retrieve cross sections
        :param sqrts: center of mass energies
        :param slhafile: SLHA file
        :param ssmultipliers: optionally supply signal strengh multipliers,
                given as dictionary of the tuple of the mothers' pids as keys and
                multipliers as values, e.g { (1000001,1000021):1.1 }.
        :returns: List of cross sections to be added
        """
        channels = self.findOpenChannels ( slhafile )
        xsecs = crossSection.XSectionList()
        for channel in channels:
            # obtain xsecs for all masses, but for the given channel
            # for sqrts in self.sqrtses: # FIXME
            pids = channel["pids"]
            xsecall,order,comment = self.getXSecsFor ( pids[0], pids[1], sqrts, "" )
            ## interpolate for the mass that we are looking for
            if xsecall == None:
                continue
            xsec = self.interpolate ( channel["masses"][0], xsecall )
            if xsec == None:
                continue
            if ssmultipliers != None and ( pids[1], pids[0] ) in ssmultipliers:
                pids = ( pids[1], pids[0] )
            if ssmultipliers != None and pids in ssmultipliers:
                ssm = ssmultipliers[pids]
                channel["ssm"] = ssm
                xsec = xsec * ssm
            channel["xsec"] = xsec
            channel["sqrts"] = sqrts
            channel["order"] = order
            channel["comment"] = comment
            orderStr = crossSection.orderToString(order,False,False)
            channel["label"] = f"{int(sqrts)} TeV ({orderStr})"
            xsecs.add ( self.dictToXSection ( channel ) )
        self.xsecs = xsecs
        return xsecs

    def findOpenChannels ( self, slhafile ):
        slhadata = pyslha.readSLHAFile ( slhafile )
        masses = slhadata.blocks["MASS"]
        # print ( "findOpenChannels" )
        channels = []
        # productions of same-sign-pid pairs when the particle is within reach
        samesignmodes = ( 1000021, )
        # production of opposite-sign-pid pairs when the particle is within reach
        oppositesignmodes = ( 1000006, 1000005, 1000011, 1000013, 1000015 )

        # associate production
        associateproduction = ( ( 1000001, 1000021 ), ( 1000022, 1000023 ) )
        ## production modes to add that needs to different particles
        ## to be unfrozen
        associateproductions = { ( 1000001, 1000021 ): ( 1000001, 1000021 ) }

        for pid,mass in masses.items():
            if pid < 999999:
                continue
            if mass > 5000:
                continue

            if pid in samesignmodes:
                channels.append ( { "pids": (pid,pid), "masses": ( mass, mass ) } )
            if pid in oppositesignmodes:
                channels.append ( { "pids": (-pid,pid), "masses": ( mass, mass ) } )
            for jpid, jmass in masses.items():
                if pid >= jpid:
                    continue
                if (pid,jpid) in associateproduction:
                    channels.append ( { "pids": (jpid,pid), "masses": (jmass, mass ) } )
        if len(channels)==0:
            print ( f"[refxsecComputer] found no open channels for {slhafile}" )
        return channels

    def interpolate ( self, mass, xsecs ):
        """ interpolate between masses """
        if mass in xsecs:
            return xsecs[mass]
        if mass < min(xsecs.keys()):
            logger.info ( "mass %d<%d too low to interpolate, leave it as is."  % ( mass, min(xsecs.keys() ) ) )
            return None
        if mass > max(xsecs.keys()):
            logger.info ( "mass %d>%d too high to interpolate, leave it as is." % ( mass, max(xsecs.keys() ) ) )
            return None
        from scipy.interpolate import interp1d
        return interp1d ( list(xsecs.keys()), list(xsecs.values()) )( mass )

    def getXSecsFrom ( self, path, pb = True, columns={"mass":0,"xsec":1 } ):
        """ retrieve xsecs from filename
        :param pb: xsecs given in pb
        :param indices: the indices of the columns in the table, for mass and xsec
        """
        ret = {}
        if not os.path.exists ( path ):
            logger.info ( "could not find %s" % path )
            return ret
        logger.info ( "getting xsecs from %s" % path )
        f = open ( path, "rt" )
        lines=f.readlines()
        f.close()
        for line in lines:
            if line.find("#")>-1:
                line = line[:line.find("#")]
            if "mass [GeV]" in line: ## skip
                continue
            tokens = line.split ()
            if len(tokens)<2:
                continue
            mass = float(tokens[ columns["mass"] ])
            xsec = float(tokens[ columns["xsec"] ].replace("GeV","") )
            if not pb:
                xsec = xsec / 1000.
            ret[ mass ] = xsec
        return ret

    def getXSecsFor ( self, pid1, pid2, sqrts, ewk ):
        """ get the xsec dictionary for pid1/pid2, sqrts
        :param ewk: specify the ewkino process (hino, or wino)
        """
        filename=None
        order = 0
        pb = True
        columns = { "mass": 0, "xsec": 1 }
        isEWK=False
        comment="refxsec [pb]"
        if pid1 in [ 1000021 ] and pid2 == pid1:
            filename = "xsecgluino%d.txt" % sqrts
            columns["xsec"]=2
            isEWK=False
            order = NNLL # 4
        if pid1 in [ -1000024 ] and pid2 in [ 1000023 ]:
            filename = "xsecN2C1m%d.txt" % sqrts
            order = NLL
            isEWK=True
            pb = False
        if pid1 in [ 1000023 ] and pid2 in [ 1000024 ]:
            filename = "xsecN2C1p%d.txt" % sqrts
            order = NLL
            pb = False
            isEWK=True
        if pid1 in [ 1000023 ] and pid2 in [ 1000022 ]:
            if sqrts == 8:
                print ( "[refxsecComputer] asking for N2 N1 production for 8 TeV. we only have 13 tev" )
                return None, None, None
            filename = "xsecN2N1p%d.txt" % sqrts
            order = NLL
            pb = False
            isEWK=True
        if pid1 in [ 1000024 ] and pid2 in [ 1000025 ]:
            filename = "xsecN2C1p%d.txt" % sqrts
            order = NLL
            pb = False
            isEWK=True
        if pid1 in [ -1000024 ] and pid2 in [ 1000025 ]:
            filename = "xsecN2C1m%d.txt" % sqrts
            order = NLL
            isEWK=True
            pb = False
        if pid1 in [ -1000005, -1000006, -2000006 ] and pid2 == -pid1:
            ## left handed slep- slep+ production.
            filename = "xsecstop%d.txt" % sqrts
            order = NNLL #3
            columns["xsec"]=2
            pb = True
        if pid1 in [ -1000024 ] and pid2 == -pid1:
            ## left handed slep- slep+ production.
            filename = "xsecC1C1%d.txt" % sqrts
            order = NLL #3
            pb = False
        if pid1 in [ -1000011, -1000013, -1000015 ] and pid2 == -pid1:
            ## left handed slep- slep+ production.
            filename = "xsecslepLslepL%d.txt" % sqrts
            order = NLL #3
        if pid1 in [ -2000011, -2000013, -2000015 ] and pid2 == -pid1:
            filename = "xsecslepRslepR%d.txt" % sqrts
            order = NLL # 3
        if filename == None:
            logger.info ( "could not identify filename for xsecs" )
            logger.info ( "seems like we dont have ref xsecs for the pids %d/%d?" % ( pid1, pid2 ) )
            return None, None, None
            # sys.exit()
        if ewk == "hino":
            filename = filename.replace(".txt","hino.txt" )
        if isEWK:
            comment = " (%s)" % ewk
        path = os.path.join ( self.shareDir, filename )
        if not os.path.exists ( path ):
            logger.info ( "%s missing" % path )
            sys.exit()
        xsecs = self.getXSecsFrom ( path, pb, columns )
        return xsecs,order,comment

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser( description = "compute xsecs by looking up reference cross sections" )
    argparser.add_argument ( "-f", "--inputfile",
            help="slha file [./simplyGluino.slha]",
            type=str, default="./simplyGluino.slha" )
    args = argparser.parse_args()
    setLogLevel ( "debug" )
    tool = RefXSecComputer()
    # slhafile = "inputFiles/slha/simplyGluino.slha"
    # slhapath = os.path.join ( smodelsinstallation.installDirectory(), slhafile )
    # slhapath = "./simplyGluino.slha"
    slhapath = args.inputfile
    # logger.info ( "slhafile: " + slhapath )
    # slhafile = "./test.slha"
    # output = tool.compute(slhapath )
    tool.computeForOneFile ( sqrtses=[8, 13], inputFile = slhapath, tofile=True,
                             ssmultipliers = { (1000021,1000021):2. } )
    # logger.info ( "done: %s" % output )
