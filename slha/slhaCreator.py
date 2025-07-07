#!/usr/bin/env python3

"""
.. module:: slhaCreator
   :synopsis: Main methods for generating SLHA files for a given Txname from a
              template

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,shutil
sys.path.append('../../smodels/')
sys.path.append('../../smodels-utils/')

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)
import tempfile
import pyslha
import math, numpy, subprocess, time, sys, os
from smodels.decomposition import decomposer
from smodels.base.physicsUnits import fb, GeV, TeV
from smodels.base import runtime
from smodels.tools import xsecComputer
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from validation.pythiaCardGen import getPythiaCardFor
from smodels_utils.helper.terminalcolors import *
import signal
from typing import Union

__tempfiles__ = set()

def removeTempFiles( verbose : bool = False ):
    for l in __tempfiles__:
        if l == None:
            continue
        if not os.path.exists ( l ):
            continue
        cmd = f"rm -rf {l}"
        subprocess.getoutput ( cmd )
        if verbose:
            print ( f"[slhaCreator] {cmd}" )
    __tempfiles__.clear()

def signal_handler(sig, frame):
    if len(__tempfiles__)>0:
        # print( f'[slhaCreator] You pressed Ctrl+C, remove {len(__tempfiles__)} temporary files!')
        removeTempFiles()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

complaints = { "removingSLHAFile": 0 }

class TemplateFile(object):
    """
    Holds the information for a given template file as well as convenient methods
    for generating SLHA files.
    """

    def __init__(self,topology,axes,tempdir=None,pythiaVersion : int =6,
                 keep : bool = False, txName : Union[None,str] = None,
                 add_pids : Union[None,str] = None, verbose : bool = False ):
        """
        :param topology: the txname
        :param axes: string describing the axes for the template file
                    (i.e. 2*Eq(mother,x)_Eq(inter0,y)_Eq(lsp,x-80.0))
        :param tempdir: Folder to store the SLHA files. If not set,
                        a temporary folder will be created at the current location.
        :param pythiaVersion: Version of pythia to use (6 or 8). It specifies how
                              the pythiaCard will be generated.
        :param add_pids: if not None, list of pids to add to list of potential mother pids
        :param keep: keep temporary files
        :param verbose: if true, then print more info
        """
        template= f"../slha/templates/{topology}.template"
        if not os.path.exists ( template ):
            print ( f"[slhaCreator] error: templatefile {template} not found." )
            sys.exit()

        self.version = "1.3" ## slhaCreator version
        self.verbose = verbose
        self.add_pids = add_pids
        if add_pids in [ "None" ]:
            self.add_pids = None
        if type ( add_pids ) == str:
            self.add_pids = eval ( add_pids )
        if type ( self.add_pids ) in [ int, float ]:
            self.add_pids = [ int(self.add_pids) ]
        self.path = template
        self.txName = topology
        self.slhaObj = None
        self.ewk = None
        self.nprocesses = -1
        self.tags = []
        self.axes = axes
        self.keep = keep
        self.motherPDGs = []
        self.pythiaCard = None
        self.pythiaVersion = pythiaVersion
        if tempdir:
            self.tempdir = tempdir
        else:
            self.tempdir = tempfile.mkdtemp(dir=os.getcwd())
            print ( f"[slhaCreator] tempdir at {self.tempdir}" )
            if not self.keep:
                __tempfiles__.add ( self.tempdir )
        #Loads the information from the template file and store the axes labels
        if not os.path.isfile(template):
            logger.error( f"Template file {template} not found." )
            sys.exit()
        try:
            self.slhaObj = pyslha.readSLHAFile(template)
        except pyslha.ParseError as e:
            logger.error ( f"This file cannot be parsed as an SLHA file: {e}" )
            sys.exit()
        for pdg,mass in self.slhaObj.blocks['MASS'].items():
            if isinstance(mass,str):
                self.tags.append(mass)
                if mass == 'M0' or mass == 'm0': self.motherPDGs.append(pdg)
        ## the tags for the widths are harder to get
        self.findWidthTags( template )
        if "ISR" in self.txName:
            print ( f"[slhaCreator] this is an ISR topology, adding 1000022 to the mother pids" )
            self.motherPDGs.append ( 1000022 )
        if self.add_pids != None:
            for a in self.add_pids:
                self.motherPDGs.append( a )
        if self.motherPDGs:
            self.motherPDGs = list ( set ( self.motherPDGs ) )
            self.motherPDGs.sort()

        if self.motherPDGs:
            print ( f"[slhaCreator] setting things up with the following potential mother pids: {' '.join(map(str,self.motherPDGs))}" )
            self.pythiaCard = getPythiaCardFor(self.motherPDGs,pythiaVersion=pythiaVersion)
            if not self.keep:
                __tempfiles__.add ( self.pythiaCard )
        #Define original plot
        self.massPlane = MassPlane.fromString(None,self.axes)

    def writeOutCoordinates ( self, directory : os.PathLike ):
        """ write the entry in ../validation/filenameCoords.py
        """
        if not hasattr ( self, "coordDicts" ):
            print ( f"[slhaCreator] when trying to write out coordinates: no coordDicts available" )
            return
        fpath = f"{directory}/coordinates"
        f = open ( fpath, "wt" )
        f.write ( f"{self.coordDicts}\n" )
        f.close()
        fpath = "../validation/filenameCoords.py"
        f = open ( fpath, "rt" )
        lines = f.readlines()
        f.close()
        D={}
        exec("\n".join(lines),D)
        tempf = "../validation/filenameCoords2.py"
        g = open ( tempf, "wt" )
        for line in lines:
            if not '"'+self.txName+'"' in line:
                g.write ( line )
        g.write ( f'coords["{self.txName}"]={self.coordDicts}\n' )
        g.close()
        f2 = open ( tempf, "rt" )
        lines = f2.readlines()
        f2.close()
        D2={}
        exec("\n".join(lines),D2)
        if D==D2:
            print ( f"[slhaCreator] {fpath} did not change." )
        else:
            cmd = f"cp {tempf} {fpath}"
            subprocess.getoutput ( cmd )
            print ( f"[slhaCreator] Updated {fpath}, please make sure you git-push." )
        os.unlink ( tempf )

    def findWidthTags ( self, filename ):
        """ in a template file <template>, search for "width tags",
        e.g. W0, W1 """
        # print ( "find width tags" )
        with open(filename) as f:
            lines = f.readlines()
            for line in lines:
                p = line.find("#")
                if p > -1:
                    line = line[:p]
                if not "decay" in line.lower():
                    continue
                if not "w" in line.lower():
                    continue
                tokens = line.split()
                # print ( tokens )
                for t in tokens:
                    if t.startswith("W") or t.startswith("w"):
                        self.tags.append(t)

    def createFileFor( self,ptDict,slhaname=None,computeXsecs=False,
               massesInFileName = False, nevents = 10000, sqrts=None,
               reference_xsecs = False, swapBranches = False, ignore_pids = None ):
        """
        Creates a new SLHA file from the template.
        The entries on the template are replaced by the x,y values in pt.
        OBS: The cross-sections blocks from the template file are never copied to the new file.
        :param ptDict: Dictionary with coordinate values (e.g. {'x' : 10., 'y': 200.})
        :param slhaname: filename for the new file. If None, a random name for the file will be generated,
                     with prefix template and suffix .slha
        :param computeXsecs: if True, will compute NLL cross-sections for the file using 10k events
        :param massesInFileName: if True, put the masses in the name of the slha file (eg T5WW_2200_1300_60_2200_1300_60.slha)
        :param nevents: how many events to generate
        :param sqrts: sqrtses (list)
        :param reference_xsecs: if true, then use ref xsec computer to compute xsecs
        :param swapBranches: if true, swap branches in filenames
        :param ignore_pids: if not None, pids to ignore when computing xsecs (works currently only with ref xsecs)
        :return: SLHA file name if file has been successfully generated, False otherwise.
        """
        if sqrts == None:
           sqrts = [[8,13]]

        masses = self.massPlane.getParticleMasses(**ptDict)
        #if self.verbose:
        #    print ( f"[slhaCreator] create {masses}" )
        massDict = {}
        # print ( "masses=", masses )
        for ibr,br in enumerate(masses):
            massTag, widthTag = 'M', 'W'
            if ibr == 1: massTag, widthTag = 'm','W'
            for im,m in enumerate(br):
                # print ( "[slhaCreator] m", m, type(m), "tag", widthTag, "im", im )
                if type(m)==tuple:
                    massDict[massTag+str(im)] = m[0]
                    massDict[widthTag+str(im)] = m[1] ## coordinateToWidth(m[1])
                else:
                    massDict[massTag+str(im)] = m

        # print ( "massDict", massDict )
        #First check if all the axes labels defined in the template appears in massDict
        if not set(self.tags).issubset(set(massDict.keys())):
            logger.info( f"Labels do not match the ones defined in {self.path}. keys={set(massDict.keys())}. tags={set(self.tags)} (might mean only that we dont use these labels)." )
            # sys.exit()
        #Replace the axes labels by their mass values:
        ftemplate = open(self.path,'r')
        fdata = ftemplate.read()
        ftemplate.close()
        for tag in massDict:
            fdata = fdata.replace(tag+"-5",str(massDict[tag]-5))
            fdata = fdata.replace(tag,str(massDict[tag]))

        self.coordDicts = { "masses": [], "widths": None }
        #Create SLHA filename (if not defined)
        if not slhaname:
            templateName = self.path[self.path.rfind("/")+1:self.path.rfind(".")]
            if not massesInFileName:
                slhaname = tempfile.mkstemp(prefix=templateName+"_",suffix=".slha",dir=self.tempdir)
                os.close(slhaname[0])
                slhaname = slhaname[1]
            else:
                slhaname = f"{templateName}"
                if swapBranches:
                    masses = [ masses[1], masses[0] ]
                ctr = 1
                for br in masses:
                    self.coordDicts["masses"].append([])
                    if self.coordDicts["widths"]!=None:
                        self.coordDicts["widths"].append([])
                    for m in br:
                        if type(m)==tuple:
                            self.coordDicts["masses"][-1].append(ctr)
                            slhaname += "_%d_%.2g" % (m[0],m[1] )
                            if self.coordDicts["widths"]==None:
                                self.coordDicts["widths"]=[[]]
                            self.coordDicts["widths"][-1].append(ctr+1)
                            ctr+=2
                        else:
                            self.coordDicts["masses"][-1].append(ctr)
                            slhaname += "_%d" % m
                            ctr+=1
                slhaname += ".slha"
                slhaname = os.path.join(self.tempdir,slhaname)

        fdata = fdata[:fdata.find('XSECTION')]

        #Save file
        fslha = open(slhaname,'w')
        fslha.write(fdata)
        fslha.close()

        logger.info( f"File {slhaname} created." )

        return slhaname

    def createFilesFor( self, pts, massesInFileName=False, computeXsecs=False,
                        nevents = 10000, sqrts = None, reference_xsecs=False,
                        swapBranches = False, ignore_pids = None, 
                        comment : Union[None,str] = None ):
        """
        Creates new SLHA files from the template for the respective (x,y) values
        in pts.
        For each distinct x value, new cross-sections will be computed.
        :param pts: list of dicts with values for the plot in GeV
                    (e.g. [{'x' : x1, 'y' : y1}, {'x' : x2, 'y' : y2}, ...])
        :param nevents: number of events to generate
        :param sqrts: sqrtses (list)
        :param reference_xsecs: if true, then use ref xsec computer to compute xsecs
        :param swapBranches: if true, swap branches in filenames
        :param ignore_pids: if not None, pids to ignore when computing xsecs (Works currently only with ref xsecs)
        :param comment: comment to be added to all files
        :return: list of SLHA file names generated.
        """

        if sqrts == None:
           sqrts = [[8,13]]

        slhafiles = []
        first = True
        for pt in pts:
            slhafile = self.createFileFor( pt, computeXsecs=False,
                     massesInFileName=massesInFileName, nevents=nevents, sqrts=sqrts,
                     swapBranches = swapBranches, ignore_pids = ignore_pids )
            if slhafile:
                slhafiles.append(slhafile)

            if reference_xsecs:
                from smodels_utils.morexsecs.refxsecComputer import RefXSecComputer
                computer = RefXSecComputer( self.verbose, first )
                c = f"produced via slhaCreator v{self.version}"
                if comment != None:
                    c+= f": {comment}"
                if self.ewk != "wino":
                    c+= f" [{self.ewk}]"
                computer.computeForOneFile ( sqrts[0], slhafile, True, \
                          comment = c, ignore_pids = ignore_pids,
                          ewk = self.ewk )
                first = False

        # print ( f"[slhaCreator] now calling xseccomputer {computeXsecs} {self.pythiaVersion}" )
        #Compute cross-sections
        if computeXsecs:
            if self.verbose:
                print ( f"[slhaCreator] now compute xsecs for {len(slhafiles)} files on {self.nprocesses} cores" )
            if self.pythiaCard:
                xargs = argparse.Namespace()
                xargs.pythia6 = False
                xargs.pythia8 = True
                if self.pythiaVersion == 6:
                    xargs.pythia6 = True
                    xargs.pythia8 = False
                xargs.sqrts = sqrts
                xargs.ncpus = self.nprocesses
                xargs.nevents = nevents
                xargs.pythiacard = self.pythiaCard
                xargs.NLL = True
                xargs.tofile = False
                xargs.alltofile = True
                xargs.keep=False
                xargs.LOfromSLHA = False
                xargs.query = False
                xargs.colors = None
                xargs.verbosity = 30
                if self.verbose:
                    xargs.verbosity = 17
                # xargs.filename = slhafiles
                if type(ignore_pids) in [ str ]:
                    try:
                        ignore_pids = eval ( ignore_pids )
                    except (SyntaxError,Exception) as e:
                        logger.error ( f"I do not understand --ignore_pids {ignore_pids}: {e}. Aborting." )
                        sys.exit()
                if type(ignore_pids) in [ list, tuple ]:
                    ssms = { x: 0.0 for x in ignore_pids }
                    xargs.ssmultipliers = ssms
                xargs.filename = self.tempdir
                xsecComputer.main(xargs)
        return slhafiles

    def addToRecipe ( self, directory, command ):
        """ add our current command to the recipe file """
        # print ( f"adding to recipe {directory}" )
        with open ( f"{directory}/recipe", "at" ) as f:
            f.write ( f"\n# slhaCreator v{self.version}, {time.asctime()}:\n{command}\n" )
            f.close()

    def checkFor(self,txnameObj,x,y,z=None):
        """
        Run SModels in the template file with the x,y values and check if it returns
        at least one of the elements belonging to the txnameObj.
        Also verifies if the masses are the ones given by x,y.
        :param txnameObj: a TxName object holding information about the txname
        :param x: x value for the plot in GeV (i. e. mother mass).
        :param y: y value for the plot in GeV (i. e. lsp mass).
        :param z: z value for the plot in GeV (only for 3D grids).
        """


        inmasses = self.massPlane.getParticleMasses(x=x, y=y, z=z)
        #Add units:
        inmasses = [[m*GeV for m in br] for br in inmasses]

        #First create temporary file:
        tempSLHA = self.createFileFor(x,y,z)
        if not tempSLHA: return False
        #Add cross-sections to file running only mother pair production:
        #(to guarantee the mother cross-section value is reliable)
        if self.pythiaCard:
            computerLO = XSecComputer(LO, 1000, 6)
            xsecsLO = computerLO.compute(8*TeV, tempSLHA,pythiacard=self.pythiaCard)
            computerLO.addXSecToFile(xsecsLO,tempSLHA,comment="1k events (unit = pb)")
            computerNLL = XSecComputer(NLL, 1000, 6)
            xsecsNLL = computerNLL.compute(8*TeV, tempSLHA,loFromSlha=True,
                                           pythiacard=self.pythiaCard)
            computerNLL.addXSecToFile(xsecsNLL,tempSLHA,comment="(unit = pb)")
        #Run decomposition on the file:
        sigmacut = 0.*fb
        mingap = 2.*GeV
        smstoplist = decomposer.decompose(tempSLHA, sigmacut,\
                        doCompress=True,doInvisible=True, minmassgap=mingap)

        #Delete the temporary SLHA file and pythia card
        shutil.rmtree(os.path.dirname(os.path.realpath(tempSLHA)))
        os.remove(self.pythiaCard)

        if not smstoplist or not smstoplist.getElements():
            logger.error("Decomposition produced no results.")
            return False

        allEls = smstoplist.getElements()
        goodEl = False
        for el in allEls:
            goodEl = txnameObj.hasElementAs(el)
            if goodEl:
                break

        #Check if a valid element was created:
        if not goodEl:
            logger.warning( f"No macthing element for {txnameObj.txName} generated from template" )
            return False

        #Check if the masses match
        #(allow for the case where both branching orders matches the txname):
        if inmasses != goodEl.getMasses():
            goodElB = txnameObj.hasElementAs(goodEl.switchBranches())
            if (not goodElB) or (goodElB and inmasses != goodElB.getMasses()):
                logger.warning("Masses do not seem to match")
                return False


        return True

def createMassRanges ( args ):
    """ from the commandline arguments, create the mass ranges """
    masses=[]
    excludeInvertedMasses=True # if true, dont allow daughters heavier than mothers
    if args.zmin is None:
        ## only x and y are given
        for x in numpy.arange(args.xmin,args.xmax+1,args.dx):
            if args.logy:
                if args.dy < 1.:
                    logger.error ( "y axis is log scale, but dy < 1. Did you mean 1/dy?" )
                    sys.exit()
                y = args.ymin
                while y < args.ymax:
                    if args.max_dxy != None and (x-y) > args.max_dxy:
                        continue
                    if args.min_dxy != None and (x-y) < args.min_dxy:
                        continue
                    masses.append ( { "x": x, "y": y } )
                    y = y * args.dy
            else:
                for y in numpy.arange(args.ymin,args.ymax+args.dy*.1,args.dy):
                    if excludeInvertedMasses and y > x:
                        break
                    if args.max_dxy != None and (x-y) > args.max_dxy:
                        continue
                    if args.min_dxy != None and (x-y) < args.min_dxy:
                        continue
                    masses.append ( { "x": x, "y": y } )
        return masses
    # x,y and z are given
    for x in numpy.arange(args.xmin,args.xmax+1,args.dx):
        if args.logy:
            if args.dy < 1.:
                logger.error ( "y axis is log scale, but dy < 1. Did you mean 1/dy?" )
                sys.exit()
            y = args.ymin
            while y < args.ymax:
                if args.max_dxy != None and (x-y) > args.max_dxy:
                    continue
                if args.min_dxy != None and (x-y) < args.min_dxy:
                    continue
                if args.logz:
                    if args.dz < 1.:
                        logger.error ( "z axis is log scale, but dz < 1. Did you mean 1/dz?" )
                        sys.exit()
                    z = args.zmin
                    while z < args.zmax:
                        masses.append ( { "x": x, "y": y, "z": z } )
                        z = z * args.dz
                else:
                    for z in numpy.arange(args.zmin,args.zmax+1,args.dz):
                        masses.append ( { "x": x, "y": y, "z": z } )
                y = y * args.dy
        else: ## y is not log scale, so y should be below x, we assume
            for y in numpy.arange(args.ymin,args.ymax+1.,args.dy):
                if args.max_dxy != None and (x-y) > args.max_dxy:
                    continue
                if args.min_dxy != None and (x-y) < args.min_dxy:
                    continue
                if excludeInvertedMasses and y > x:
                    break
                if args.logz:
                    if args.dz < 1.:
                        logger.error ( "z axis is log scale, but dz < 1. Did you mean 1/dz?" )
                        sys.exit()
                    z = args.zmin
                    while z < args.zmax:
                        masses.append ( { "x": x, "y": y, "z": z } )
                        z = z * args.dz
                else:
                    for z in numpy.arange(args.zmin,args.zmax+1,args.dz):
                        if excludeInvertedMasses and z > y:
                            break
                        masses.append ( { "x": x, "y": y, "z": z } )
    return masses

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description="creates slha files from template file in given mass ranges")
    argparser.add_argument ( '-t', '--topology', nargs='?', help='topology to create SLHA files for [T1]',
        type=str, default='T1' )
    argparser.add_argument ( '--tarball', help='name of tarball [@@topo@@.tar.gz]',
        type=str, default='@@topo@@.tar.gz' )
    argparser.add_argument ( '-C', '--comment', nargs='?', help='add a comment to all files [None]',
        type=str, default=None )
    argparser.add_argument ( '-e', '--ewk', help='type of ewk process, wino, hino, or degenerate [None]',
        type=str, default=None )
    argparser.add_argument ( '-a', '--axes', nargs='?', help='axes description 2*[[x, y]]',
        type=str, default='2*[[x, y]]' )
    argparser.add_argument ( '--xmin', nargs='?', help='minimum value for x [100]',
        type=float, default=100. )
    argparser.add_argument ( '--xmax', nargs='?', help='maximum value for x [300]',
        type=float, default=300. )
    argparser.add_argument ( '--dx', nargs='?', help='binning in x [25]',
        type=float, default=25. )
    argparser.add_argument ( '--ymin', nargs='?', help='minimum value for y [100]',
        type=float, default=100. )
    argparser.add_argument ( '--ymax', nargs='?', help='maximum value for y [300]',
        type=float, default=300. )
    argparser.add_argument ( '--dy', nargs='?', help='binning in y [25]',
        type=float, default=25. )
    argparser.add_argument ( '--max_dxy', nargs='?', help='maximum (x-y) [None]',
        type=float, default=None )
    argparser.add_argument ( '--min_dxy', nargs='?', help='minimum (x-y) [None]',
        type=float, default=None )
    argparser.add_argument( '-ly', '--logy', action='store_true',
        help="logarithmic scale for y axis (in which case dy is multiplicative)" )
    argparser.add_argument( '-v', '--verbose', action='store_true',
        help="be verbose" )
    argparser.add_argument ( '--zmin', nargs='?', help='minimum value for z [None]',
        type=float, default=None )
    argparser.add_argument ( '--zmax', nargs='?', help='maximum value for z [None]',
        type=float, default=None )
    argparser.add_argument ( '--dz', nargs='?', help='binning in z [50]',
        type=float, default=50. )
    argparser.add_argument( '-lz', '--logz', action='store_true',
        help="logarithmic scale for z axis (in which case dz is multiplicative)" )
    argparser.add_argument ( '-n', '--nevents', help='number of events to generate [10000]',
        type=int, default=20000 )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?', help='number of processes, -1 means one per CPU [-1].',
        type=int, default=-1 )
    argparser.add_argument('-c', '--clear', action='store_true',
        help="clear cruft files")
    argparser.add_argument ( '-s', '--sqrts', help='center-of-mass energies [8 13]',
        type=int, nargs="*", default=None )
    argparser.add_argument('-k', '--keep', action='store_true',
        help="keep temp files")
    argparser.add_argument('-r', '--reference_xsecs', action='store_true',
        help="compute cross sections via refxsecComputer")
    argparser.add_argument('-d', '--dry_run', action='store_true',
        help="dry run, only show which points would be created")
    argparser.add_argument('-o', '--overwrite', action='store_true',
        help="overwrite existing tarball, default is to append")
    argparser.add_argument('-i', '--ignore_pids', type=str, default=None,
        help="specify pids you wish to ignore when computing xsecs, e.g. '(1000023,1000023)'.")
    argparser.add_argument('-A', '--add_pids', type=str, default=None,
        help="add pids to list of candidate mother pids, e.g. '[1000022]'.")
    argparser.add_argument('--swapBranches', action='store_true',
        help="switch the order of the branches in the slha file name")
    argparser.add_argument('-6', '--pythia6', action='store_true',
        help="use pythia6 for LO cross sections")
    argparser.add_argument('-8', '--pythia8', action='store_true',
        help="use pythia8 for LO cross sections [default]")
    args=argparser.parse_args()
    if sum( [ args.pythia8, args.pythia6, args.reference_xsecs ] ) > 1:
        print ( f"[slhaCreator] error: specified more than one of the following mutually exclusive options: pythia6, pythia8, reference_xsecs" )
        sys.exit()
    if args.sqrts == None:
        args.sqrts = [ 8, 13 ]
    if args.clear:
        subprocess.getoutput ( "rm -rf tmp* pythia*card" )
        sys.exit()
    pythiaVersion = 8
    if args.pythia6:
        pythiaVersion = 6
    tarball = args.tarball.replace ( "@@topo@@", args.topology )
    if args.overwrite and os.path.exists ( tarball ):
        print ( f"[slhaCreator] {YELLOW}overwriting existing {tarball}!{RESET}" )
        os.unlink ( tarball )
    if os.path.exists ( tarball ) and not args.overwrite:
        print ( f"[slhaCreator] {YELLOW}NOT overwriting existing results from {tarball}!{RESET}" )

    tempf = TemplateFile(args.topology,args.axes,pythiaVersion=pythiaVersion,
                         keep=args.keep, add_pids = args.add_pids, verbose = args.verbose )
    tempf.nprocesses = args.nprocesses
    tempf.verbose = args.verbose
    tempf.ewk = args.ewk
    if args.nprocesses < 0:
        tempf.nprocesses = runtime.nCPUs() + args.nprocesses + 1
    if args.xmax < args.xmin:
        logger.error ( "xmax < xmin" )
        sys.exit()
    if args.ymax < args.ymin:
        logger.error ( "ymax < ymin" )
        sys.exit()
    if args.zmin is not None and args.zmax < args.zmin:
        logger.error ( "zmax < zmin" )
        sys.exit()
    masses = createMassRanges ( args )
    if args.dry_run:
        print ( "Dry-run: would create the following points:" )
        for pt in masses:
            if "z" in pt:
                print ( f" * x: {pt['x']}, y: {pt['y']}, z: {pt['z']}" )
            else:
                print ( f" * x: {pt['x']}, y: {pt['y']}" )
        sys.exit()
    sqrts = args.sqrts
    if sqrts == None:
        sqrts = [ 8, 13 ]
    slhafiles = tempf.createFilesFor( masses, computeXsecs = args.pythia6 or args.pythia8,
                   massesInFileName=True, nevents=args.nevents,
                   sqrts = [ sqrts ], reference_xsecs = args.reference_xsecs,
                   swapBranches = args.swapBranches, ignore_pids = args.ignore_pids, 
                   comment = args.comment )
    print ( f"[slhaCreator] Produced {len(slhafiles)} slha files" )
    # newtemp = tempfile.mkdtemp(dir="./" ) # FIXME now idea what that was for
    newtemp = tempf.tempdir # FIXME anyways this does it correctly it seems
    __tempfiles__.add ( newtemp )
    #oldtarball = f"{args.topology}.tar.gz"
    oldtarball = tarball
    if os.path.exists ( oldtarball ):
        subprocess.getoutput ( f"cp {oldtarball} prev.{oldtarball}" )
    print ( f"[slhaCreator] Now build new tarball in {newtemp}/" )
    subprocess.getoutput ( f"cd {newtemp}; tar xzvf ../../slha/{tarball}" )
    cmd = "cp {tempf.tempdir}/{args.topology}*.slha {tempf.tempdir}/recipe {tempf.tempdir}/coordinates {newtemp}"
    # print ( "cmd", cmd )
    subprocess.getoutput ( cmd )
    argvs = sys.argv
    for i,a in enumerate(argvs):
        if "(" in a or "[" in a:
            argvs[i]=f'"{a}"'
    tempf.addToRecipe ( newtemp, " ".join ( argvs ) )
    tempf.writeOutCoordinates ( newtemp )
    from slhaHelpers import hasXSecs
    import glob
    for slhafile in glob.glob ( f"{newtemp}/{args.topology}*slha" ):
        if not hasXSecs ( slhafile ) and not args.keep:
            complaints["removingSLHAFile"]+=1
            if complaints["removingSLHAFile"]<3:
                print ( f"[slhaCreator] removing {slhafile}: has no cross sections (use --keep if you want to keep them)" )
            if complaints["removingSLHAFile"]==3:
                print ( f"[slhaCreator] quenching more such messsages" )
            os.unlink ( slhafile )
    cmd = f"cd {newtemp}; tar czvf ../{tarball} {args.topology}*slha recipe coordinates"
    if False:
        print ( f"[slhaCreator] {cmd}" )
    o = subprocess.getoutput ( cmd )
    print ( f"[slhaCreator] New tarball {tarball}" )
    if not args.keep:
        removeTempFiles()
