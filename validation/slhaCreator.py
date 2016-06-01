#!/usr/bin/env python

"""
.. module:: slhaCreator
   :synopsis: Main methods for generating SLHA files for a given Txname from a template

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys
sys.path.append('../../smodels/')
sys.path.append('../../smodels-utils/')

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
import tempfile
import pyslha as modpyslha
from smodels.theory import slhaDecomposer
from smodels.tools.physicsUnits import fb, GeV, TeV
from smodels.tools.xsecComputer import computeXSec,addXSecToFile
from smodels.experiment.databaseObj import Database
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot
from validation.pythiaCardGen import getPythiaCardFor

class TemplateFile(object):
    """
    Holds the information for a given template file as well as convenient methods
    for generating SLHA files.
    """

    def __init__(self,template,axes):
        """
        :param template: path to the template file
        :param axes: string describing the axes for the template file 
                    (i.e. 2*Eq(mother,x)_Eq(inter0,y)_Eq(lsp,x-80.0))
        """
        
        self.path = template
        self.slhaObj = None
        self.tags = []
        self.axes = axes
        self.motherPDGs = []
        self.pythiaCard = None
        #Loads the information from the template file and store the axes labels
        if not os.path.isfile(template):
            logger.error("Template file %s not found." %template)
            sys.exit()
        try:
            self.slhaObj = modpyslha.readSLHAFile(template)
        except modpyslha.ParseError,e:
            logger.error ( "This file cannot be parsed as an SLHA file: %s" % e )
            sys.exit()
        for pdg,mass in self.slhaObj.blocks['MASS'].items():
            if isinstance(mass,str):
                self.tags.append(mass)
                if mass == 'M0' or mass == 'm0': self.motherPDGs.append(pdg)

        if self.motherPDGs:
            self.pythiaCard = getPythiaCardFor(self.motherPDGs)
        #Define original plot
        self.origPlot = OrigPlot.fromString(self.axes)
        

    def createFileFor(self,x,y,slhaname=None,computeXsecs=False, massesInFileName = False):
        """
        Creates a new SLHA file from the template.
        The entries on the template are replaced by the x,y values.
        OBS: The cross-sections blocks from the template file are never copied to the new file.
        :param x: x value for the plot in GeV (i. e. mother mass)
        :param y: y value for the plot in GeV (i. e. lsp mass)
        :param slhaname: filename for the new file. If None, a random name for the file will be generated,
                     with prefix template and suffix .slha
        :param computeXsecs: if True, will compute NLL cross-sections for the file using 10k events
        :return: SLHA file name if file has been successfully generated, False otherwise.
        """

        masses = self.origPlot.getParticleMasses(x, y)
        massDict = {}
        for ibr,br in enumerate(masses):
            if ibr == 0: massTag = 'M'
            elif ibr == 1: massTag = 'm'
            for im,m in enumerate(br): massDict[massTag+str(im)] = m 
            
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
                slhaname = tempfile.mkstemp(prefix=templateName+"_",suffix=".slha",dir=os.getcwd())
                os.close(slhaname[0])
                slhaname = slhaname[1]
            else:
                slhaname = "%s" % ( templateName)
                for br in masses:
                    for m in br: slhaname += "_%d" % m
                slhaname += ".slha"

        fdata = fdata[:fdata.find('XSECTION')]
        
        #Save file
        fslha = open(slhaname,'w')
        fslha.write(fdata)
        fslha.close()
                
        #Compute cross-sections
        if computeXsecs:
            if self.pythiaCard:
                xsecs = computeXSec(sqrts=8.*TeV, maxOrder=0, nevts=1000, slhafile=slhaname,
                                    pythiacard=self.pythiaCard)
                addXSecToFile(xsecs,slhaname,comment="1k events (unit = pb)")         
            xsecs = computeXSec(sqrts=8.*TeV, maxOrder=0, nevts=10000, slhafile=slhaname)
            addXSecToFile(xsecs,slhaname,comment="10k events (unit = pb)")
            xsecs = computeXSec(sqrts=8.*TeV, maxOrder=2, nevts=10000, slhafile=slhaname,
                                loFromSlha=True)
            addXSecToFile(xsecs,slhaname,comment="(unit = pb)")
            
        logger.info("File %s created." %slhaname)
        return slhaname
    
    def createFilesFor(self,pts,addXsecs=True, massesInFileName=False):
        """
        Creates new SLHA files from the template for the respective (x,y) values in pts.
        For each distinct x value, new cross-sections will be computed.  
        :param pts: list of [x,y] values for the plot in GeV (i. e. [mother mass, lsp mass])
        :param addXsecs: if True will compute the cross-sections and add them to the SLHA files.
                        OBS:  The cross-sections are computed only once per x-value
        :return: list of SLHA file names generated.
        """

        #First add the value of the mother masses for each (x,y) point:
        mpts = []
        for x,y in pts:
            mother1 = self.origPlot.getParticleMasses(x,y)[0][0]
            mother2 = self.origPlot.getParticleMasses(x,y)[1][0]
            mpts.append([[mother1,mother2],x,y])
        #Sort list of point by mother masses (to speed up xsec calculation):
        sorted_pts = sorted(mpts, key=lambda pt: pt[0])
        mother0 = None        
        slhafiles = []
        for pt in sorted_pts:
            mother = pt[0]
            x,y = pt[1],pt[2]
            slhafile = self.createFileFor(x,y,massesInFileName=massesInFileName )
            if slhafile: slhafiles.append(slhafile)
            else: continue
            if not addXsecs: continue
            #Compute cross-sections every time the x-value changes
            if not mother0 or mother0 != mother:
                if self.pythiaCard:
                    xsecsProc = computeXSec(sqrts=8.*TeV, maxOrder=0, nevts=1000, slhafile=slhafile,
                                        pythiacard=self.pythiaCard)
                    addXSecToFile(xsecsProc,slhafile,comment="1k events (unit = pb)")         
                xsecsLO = computeXSec(sqrts=8.*TeV, maxOrder=0, nevts=10000, slhafile=slhafile)
                addXSecToFile(xsecsLO,slhafile,comment="10k events (unit = pb)")
                xsecsNLL = computeXSec(sqrts=8.*TeV, maxOrder=2, nevts=10000, slhafile=slhafile,
                                       loFromSlha=True)
                addXSecToFile(xsecsNLL,slhafile,comment="(unit = pb)")
            #If the x-value did not change, simply add the previously computed xsecs to file
            else:
                if self.pythiaCard:
                    addXSecToFile(xsecsProc,slhafile,comment="1k events (unit = pb)")
                addXSecToFile(xsecsLO,slhafile,comment="10k events (unit = pb)")                
                addXSecToFile(xsecsNLL,slhafile,comment="(unit = pb)")
            mother0 = mother

        return slhafiles

    def checkFor(self,txnameObj,x,y):
        """
        Run SModels in the template file with the x,y values and check if it returns
        at least one of the elements belonging to the txnameObj.
        Also verifies if the masses are the ones given by x,y.
        :param txnameObj: a TxName object holding information about the txname
        :param x: x value for the plot in GeV (i. e. mother mass)
        :param y: y value for the plot in GeV (i. e. lsp mass)
        """
        
        inmasses = self.origPlot.getParticleMasses(x, y)
        #Add units:
        for ib,mbranch in enumerate(inmasses):
            for im,mass in enumerate(mbranch): inmasses[ib][im] = mass*GeV
                
        #First create temporary file:
        tempSLHA = self.createFileFor(x,y)
        if not tempSLHA: return False
        #Add cross-sections to file running only mother pair production:
        #(to guarantee the mother cross-section value is reliable)
        if self.pythiaCard:        
            xsecs = computeXSec(sqrts=8.*TeV, maxOrder=0, nevts=1000, slhafile=tempSLHA,
                                pythiacard=self.pythiaCard)
            addXSecToFile(xsecs,tempSLHA)
        #Now add cross-sections to file running all MSSM processes:
        #(to avoid too trivial results from the decomposition)
        xsecs = computeXSec(sqrts=8.*TeV, maxOrder=0, nevts=10000, slhafile=tempSLHA)
        addXSecToFile(xsecs,tempSLHA)
        
        #Run decomposition on the file:
        sigmacut = 0.*fb
        mingap = 5.*GeV
        smstoplist = slhaDecomposer.decompose(tempSLHA, sigmacut,\
                        doCompress=True,doInvisible=True, minmassgap=mingap)
        if not smstoplist or not smstoplist.getElements():
            logger.error("Decomposition produced no results.")
            return False
                
        allEls = smstoplist.getElements()
        goodEl = False
        for elA in txnameObj._elements:            
            if goodEl: break
            for elB in allEls:
                if elA.particlesMatch(elB):
                    goodEl = elB
                    break
        
        #Check if a valid element was created:
        if not goodEl:
            logger.warning("No macthing element for %s generated from template" %txnameObj.txname)
            return False
        
        #Check if the masses match:
        outmasses = goodEl.getMasses()
        if inmasses != outmasses:
            logger.warning("Masses do not seem to match")
            return False
        
        #Finally, delete the temporary SLHA file
        os.remove(tempSLHA)
        os.remove(self.pythiaCard)
        
        return True
        


if __name__ == "__main__":
    import argparse, types
    argparser = argparse.ArgumentParser(description="creates slha files from template file in given mass ranges")
    argparser.add_argument ( '-T', '--templatefile', nargs='?', help='path to template file', 
        type=types.StringType, default='T1' )
    argparser.add_argument ( '-a', '--axes', nargs='?', help='axes description', 
        type=types.StringType, default='2*Eq(mother,x)_Eq(lsp,y)' )
    argparser.add_argument ( '--xmin', nargs='?', help='minimum value for x', 
        type=types.FloatType, default=0. )
    argparser.add_argument ( '--xmax', nargs='?', help='maximum value for x', 
        type=types.FloatType, default=100. )
    argparser.add_argument ( '--dx', nargs='?', help='binning in x', 
        type=types.FloatType, default=20. )
    argparser.add_argument ( '--ymin', nargs='?', help='minimum value for y', 
        type=types.FloatType, default=0. )
    argparser.add_argument ( '--ymax', nargs='?', help='maximum value for y', 
        type=types.FloatType, default=100. )
    argparser.add_argument ( '--dy', nargs='?', help='binning in y', 
        type=types.FloatType, default=20. )
    args=argparser.parse_args()

    templatefile = args.templatefile
    if not os.path.exists ( templatefile ):
        templatefile="../slha/%s" % templatefile
        if not os.path.exists ( templatefile ):
            print "[slhaCreator] error: templatefile does not exist."
            import sys
            sys.exit()
    tempf = TemplateFile(args.templatefile,args.axes)
    masses=[]
    import numpy
    for mother in numpy.arange(args.xmin,args.xmax+1,args.dx):
        for lsp in numpy.arange(args.ymin,args.ymax+1,args.dy):
            masses.append ( [ mother, lsp ] )
    slhafiles = tempf.createFilesFor( masses )
    print slhafiles
