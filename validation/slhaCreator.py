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
import math
try: ## smodels <= 122
    from smodels.theory import slhaDecomposer as decomposer
except ImportError: ## smodels >= 200
    from smodels.theory import decomposer
from smodels.tools.physicsUnits import fb, GeV, TeV
from smodels.tools.xsecComputer import XSecComputer, LO, NLL
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
        :param pythiaVersion: Version of pythia to use (6 or 8). It specifies how the pythiaCard will be generated.
        """
        
        self.path = template
        self.slhaObj = None
        self.tags = []
        self.axes = axes
        self.motherPDGs = []
        self.pythiaCard = None
        if tempdir:
            self.tempdir = tempdir
        else:
            self.tempdir = tempfile.mkdtemp(dir=os.getcwd())
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

        if self.motherPDGs:
            self.pythiaCard = getPythiaCardFor(self.motherPDGs,pythiaVersion=pythiaVersion)
        #Define original plot
        self.massPlane = MassPlane.fromString(None,self.axes)
        

    def createFileFor(self,ptDict,slhaname=None,computeXsecs=False, massesInFileName = False):
        """
        Creates a new SLHA file from the template.
        The entries on the template are replaced by the x,y values in pt.
        OBS: The cross-sections blocks from the template file are never copied to the new file.
        :param ptDict: Dictionary with coordinate values (e.g. {'x' : 10., 'y': 200.})
        :param slhaname: filename for the new file. If None, a random name for the file will be generated,
                     with prefix template and suffix .slha
        :param computeXsecs: if True, will compute NLL cross-sections for the file using 10k events
        :return: SLHA file name if file has been successfully generated, False otherwise.
        """

        masses = self.massPlane.getParticleMasses(**ptDict)
        massDict = {}
        for ibr,br in enumerate(masses):
            massTag, widthTag = 'M', 'W'
            if ibr == 1: massTag, widthTag = 'm','W'
            for im,m in enumerate(br): 
                if type(m)==tuple:
                    massDict[massTag+str(im)] = m[0]
                    massDict[widthTag+str(im)] = m[1] ## coordinateToWidth(m[1])
                else:
                    massDict[massTag+str(im)] = m 
            
        #First check if all the axes labels defined in the template appears in massDict
        if not set(self.tags).issubset(set(massDict.keys())):
            logger.error("Labels do not match the ones defined in %s. keys=%s. tags=%s." % \
                ( self.path, str(set(massDict.keys())), str(set(self.tags))) )
            return False
        #Replace the axes labels by their mass values:
        ftemplate = open(self.path,'r')
        fdata = ftemplate.read()
        ftemplate.close()
        for tag in massDict: fdata = fdata.replace(tag,str(massDict[tag]))
            
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
                
        #Compute cross-sections
        if computeXsecs:
            if self.pythiaCard:
                print ( "143 add xsecs" )
                computerLO = XSecComputer(LO, 1000, 6)
                xsecsLO = computerLO.compute(8*TeV, slhaname,pythiacard=self.pythiaCard)
                computerLO.addXSecToFile(xsecsLO,slhaname,comment="1k events (unit = pb)")         
                computerNLL = XSecComputer(NLL, 1000, 6)
                xsecsNLL = computerNLL.compute(8*TeV, slhaname,loFromSlha=True,
                                               pythiacard=self.pythiaCard)
                computerNLL.addXSecToFile(xsecsNLL,slhaname,comment="(unit = pb)")         

                    
        logger.info("File %s created." %slhaname)

        return slhaname
    
    def createFilesFor( self, pts, massesInFileName=False ):
        """
        Creates new SLHA files from the template for the respective (x,y) values 
        in pts.
        For each distinct x value, new cross-sections will be computed.  
        :param pts: list of dicts with values for the plot in GeV 
                    (e.g. [{'x' : x1, 'y' : y1}, {'x' : x2, 'y' : y2}, ...])
        :return: list of SLHA file names generated.
        """

        slhafiles = []        
        for pt in pts:
            slhafile = self.createFileFor(pt,massesInFileName=massesInFileName)
            if slhafile:
                slhafiles.append(slhafile)

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
            print ( "208 add xsecs" )
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
        


if __name__ == "__main__":
    import argparse, types
    argparser = argparse.ArgumentParser(description="creates slha files from template file in given mass ranges")
    argparser.add_argument ( '-T', '--templatefile', nargs='?', help='path to template file', 
        type=types.StringType, default='T1' )
    argparser.add_argument ( '-a', '--axes', nargs='?', help='axes description', 
        type=types.StringType, default='2*Eq(mother,x)_Eq(lsp,y)' )
    argparser.add_argument ( '--xmin', nargs='?', help='minimum value for x', 
        type=types.FloatType, default=100. )
    argparser.add_argument ( '--xmax', nargs='?', help='maximum value for x', 
        type=types.FloatType, default=300. )
    argparser.add_argument ( '--dx', nargs='?', help='binning in x', 
        type=types.FloatType, default=25. )
    argparser.add_argument ( '--ymin', nargs='?', help='minimum value for y', 
        type=types.FloatType, default=100. )
    argparser.add_argument ( '--ymax', nargs='?', help='maximum value for y', 
        type=types.FloatType, default=300. )
    argparser.add_argument ( '--dy', nargs='?', help='binning in y', 
        type=types.FloatType, default=25. )
    args=argparser.parse_args()

    templatefile = args.templatefile
    if not os.path.exists ( templatefile ):
        templatefile="../slha/%s" % templatefile
        if not os.path.exists ( templatefile ):
            print ( "[slhaCreator] error: templatefile does not exist." )
            sys.exit()
    tempf = TemplateFile(args.templatefile,args.axes)
    masses=[]
    import numpy
    for mother in numpy.arange(args.xmin,args.xmax+1,args.dx):
        for lsp in numpy.arange(args.ymin,args.ymax+1,args.dy):
            masses.append ( [ mother, lsp ] )
    slhafiles = tempf.createFilesFor( masses )
    print ( slhafiles )
