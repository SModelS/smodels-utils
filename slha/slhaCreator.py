#!/usr/bin/env python3

"""
.. module:: slhaCreator
   :synopsis: Main methods for generating SLHA files for a given Txname from a
              template

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function

import logging,os,sys,shutil
sys.path.append('../../smodels/')
sys.path.append('../../smodels-utils/')

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)
import tempfile
import pyslha
import math, numpy, subprocess
try: ## smodels <= 122
    from smodels.theory import slhaDecomposer as decomposer
except ImportError: ## smodels >= 200
    from smodels.theory import decomposer
from smodels.tools.physicsUnits import fb, GeV, TeV
from smodels.tools import xsecComputer, runtime
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from validation.pythiaCardGen import getPythiaCardFor

class TemplateFile(object):
    """
    Holds the information for a given template file as well as convenient methods
    for generating SLHA files.
    """

    def __init__(self,template,axes,tempdir=None,pythiaVersion=6):
        """
        :param template: path to the template file
        :param axes: string describing the axes for the template file
                    (i.e. 2*Eq(mother,x)_Eq(inter0,y)_Eq(lsp,x-80.0))
        :param tempdir: Folder to store the SLHA files. If not set,
                        a temporary folder will be created at the current location.
        :param pythiaVersion: Version of pythia to use (6 or 8). It specifies how
                              the pythiaCard will be generated.
        """

        self.path = template
        self.slhaObj = None
        self.nprocesses = -1
        self.tags = []
        self.axes = axes
        self.motherPDGs = []
        self.pythiaCard = None
        self.pythiaVersion = pythiaVersion
        if tempdir:
            self.tempdir = tempdir
        else:
            self.tempdir = tempfile.mkdtemp(dir=os.getcwd())
            print ( "[slhaCreator] tempdir at %s" % self.tempdir )
        #Loads the information from the template file and store the axes labels
        if not os.path.isfile(template):
            logger.error("Template file %s not found." %template)
            sys.exit()
        try:
            self.slhaObj = pyslha.readSLHAFile(template)
        except pyslha.ParseError as e:
            logger.error ( "This file cannot be parsed as an SLHA file: %s" % e )
            sys.exit()
        for pdg,mass in self.slhaObj.blocks['MASS'].items():
            if isinstance(mass,str):
                self.tags.append(mass)
                if mass == 'M0' or mass == 'm0': self.motherPDGs.append(pdg)
        ## the tags for the widths are harder to get
        self.findWidthTags( template )


        if self.motherPDGs:
            self.pythiaCard = getPythiaCardFor(self.motherPDGs,pythiaVersion=pythiaVersion)
        #Define original plot
        self.massPlane = MassPlane.fromString(None,self.axes)


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
                       massesInFileName = False, nevents = 10000, sqrts=None ):
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
        :return: SLHA file name if file has been successfully generated, False otherwise.
        """
        if sqrts == None:
           sqrts = [[8,13]]

        masses = self.massPlane.getParticleMasses(**ptDict)
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
            logger.info("Labels do not match the ones defined in %s. keys=%s. tags=%s (might imply only that we labels that wont get used)." % \
                ( self.path, str(set(massDict.keys())), str(set(self.tags))) )
            # sys.exit()
        #Replace the axes labels by their mass values:
        ftemplate = open(self.path,'r')
        fdata = ftemplate.read()
        ftemplate.close()
        for tag in massDict: 
            fdata = fdata.replace(tag+"-5",str(massDict[tag]-5))
            fdata = fdata.replace(tag,str(massDict[tag]))

        #Create SLHA filename (if not defined)
        if not slhaname:
            templateName = self.path[self.path.rfind("/")+1:self.path.rfind(".")]
            if not massesInFileName:
                slhaname = tempfile.mkstemp(prefix=templateName+"_",suffix=".slha",dir=self.tempdir)
                os.close(slhaname[0])
                slhaname = slhaname[1]
            else:
                slhaname = "%s" % (templateName)
                for br in masses:
                    for m in br:
                        if type(m)==tuple:
                            slhaname += "_%d_%.2g" % (m[0],m[1] )
                        else:
                            slhaname += "_%d" % m
                slhaname += ".slha"
                slhaname = os.path.join(self.tempdir,slhaname)

        fdata = fdata[:fdata.find('XSECTION')]

        #Save file
        fslha = open(slhaname,'w')
        fslha.write(fdata)
        fslha.close()

        logger.info("File %s created." %slhaname)

        return slhaname

    def createFilesFor( self, pts, massesInFileName=False, computeXsecs=False,
                        nevents = 10000, sqrts = None ):
        """
        Creates new SLHA files from the template for the respective (x,y) values
        in pts.
        For each distinct x value, new cross-sections will be computed.
        :param pts: list of dicts with values for the plot in GeV
                    (e.g. [{'x' : x1, 'y' : y1}, {'x' : x2, 'y' : y2}, ...])
        :param nevents: number of events to generate
        :param sqrts: sqrtses (list)
        :return: list of SLHA file names generated.
        """
                
        if sqrts == None:
           sqrts = [[8,13]]

        slhafiles = []
        for pt in pts:
            slhafile = self.createFileFor( pt, computeXsecs=False,
                                      massesInFileName=massesInFileName, nevents=nevents,
                                      sqrts=sqrts )
            if slhafile:
                slhafiles.append(slhafile)
        #Compute cross-sections
        if computeXsecs:
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
                xargs.filename = self.tempdir
                xsecComputer.main(xargs)

        return slhafiles

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
            logger.warning("No macthing element for %s generated from template" %txnameObj.txName)
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
                for y in numpy.arange(args.ymin,args.ymax+1,args.dy):
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
    argparser.add_argument ( '-a', '--axes', nargs='?', help='axes description 2*[[x, y, 60.]]',
        type=str, default='2*[[x, y, 60.]]' )
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
    argparser.add_argument('-X', '--xsecs', action='store_true',
        help="compute cross sections via pythia")
    argparser.add_argument('-d', '--dry_run', action='store_true',
        help="dry run, only show which points would be created")
    argparser.add_argument('-6', '--pythia6', action='store_true',
        help="use pythia6 for LO cross sections")
    argparser.add_argument('-8', '--pythia8', action='store_true',
        help="use pythia8 for LO cross sections [default]")
    args=argparser.parse_args()
    if args.clear:
        subprocess.getoutput ( "rm -rf tmp* pythia*card" )
        sys.exit()
    pythiaVersion = 8
    if args.pythia6:
        pythiaVersion = 6

    templatefile="../slha/templates/%s.template" % args.topology
    if not os.path.exists ( templatefile ):
        print ( "[slhaCreator] error: templatefile %s not found." %
                templatefile )
        sys.exit()
    tempf = TemplateFile(templatefile,args.axes,pythiaVersion=pythiaVersion)
    tempf.nprocesses = args.nprocesses
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
                print ( " * x: %s, y: %s, z: %s" % (pt["x"], pt["y"], pt["z"]) )
            else:
                print ( " * x: %s, y: %s" % (pt["x"], pt["y"]) )
        sys.exit()
    sqrts = args.sqrts
    if sqrts == None:
        sqrts = [ 8, 13 ]
    slhafiles = tempf.createFilesFor( masses, computeXsecs = args.xsecs, 
                       massesInFileName=True, nevents=args.nevents, 
                       sqrts = [ sqrts ] )
    print ( "Produced %s slha files" % len(slhafiles ) )
    newtemp = tempfile.mkdtemp(dir="./" )
    print ( "Now build new tarball in %s/" % newtemp )
    subprocess.getoutput ( "cd %s; tar xzvf ../../slha/%s.tar.gz" % \
                           ( newtemp, args.topology ) )
    subprocess.getoutput ( "cp %s/%s*.slha %s" % ( tempf.tempdir, args.topology, newtemp ) )
    subprocess.getoutput ( "cd %s; tar czvf ../%s.tar.gz %s*slha" % ( newtemp, args.topology, args.topology ) )
    print ( "New tarball %s.tar.gz" % args.topology )
    if not args.keep:
        subprocess.getoutput ( "rm -rf %s" % tempf.tempdir )
        subprocess.getoutput ( "rm -rf %s" % newtemp )

