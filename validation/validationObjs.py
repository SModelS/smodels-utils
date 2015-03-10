#!/usr/bin/env python

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a single validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys
sys.path.append('../../smodels/')

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import fb, GeV
from gridSModelS import runSModelSFor
from plottingFuncs import createPlot, getExclusionCurvesFor

logger.setLevel(level=logging.DEBUG)



class ValidationPlot():
    """
    Encapsulates all the data necessary for creating a single validation plot.
    """

    def __init__(self, ExptRes, TxNameStr, Axes, slhadir=None, databasePath=None,
                 kfactor = 1.):

        self.expRes = ExptRes
        self.txname = TxNameStr
        self.axes = Axes
        self.slhaDir = None
        self.data = None
        self.officialCurve = self.getOfficialCurve()
        self.kfactor = kfactor

        if slhadir: self.setSLHAdir(slhadir)
        if databasePath:
            if os.path.isdir(databasePath):
                self.database = databasePath
            else:
                logger.error("Database folder "+databasePath+" does not exist")
                sys.exit()
        #Try to guess the path:
        else:
            anaID = ExptRes.getValuesFor('id')
            self.database = ExptRes.path[:ExptRes.path.find('/'+anaID)]
            self.database = self.database[:self.database.rfind('/')]
            self.database = self.database[:self.database.rfind('/')+1]
            if not os.path.isdir(self.database):
                logger.error("Could not define database folder")
                sys.exit()

    def __str__(self):

        vstr = "Validation plot for\n"
        vstr += 'id: '+self.expRes.getValuesFor('id')+'\n'
        vstr += 'TxName: '+self.txname+'\n'
        vstr += 'Axes: '+self.axes
        return vstr

    def computeAgreementFactor ( self, looseness=1.2 ):
        """ computes how much the plot agrees with the official exclusion curve
            by counting the points that are inside/outside the official
            exclusion curve, and comparing against the points' r values
            ( upper limit / predict theory cross section )
            :param looseness: how much do we loosen the criterion? I.e. by what factor do we
            change the cross sections in favor of getting the right assignment?
        """
        curve=self.getOfficialCurve()
        if not curve:
            logger.error( "could not get official tgraph curve for %s %s %s" % ( self.expRes,self.txname,self.axes  ) )
            return 1.0
        curve.SetPoint( curve.GetN()+1,0.,0.) ## close the curve nicely
        n_points=0
        pts= { "total": 0, "excluded_inside": 0, "excluded_outside": 0, "not_excluded_inside": 0,
               "not_excluded_outside": 0, "wrong" : 0 }
        for point in self.data:
            x,y=point["axes"][0],point["axes"][1]
            if y==0: y=1.5 ## to avoid points sitting on the line
            excluded = point["UL"] < point["signal"]
            really_excluded = looseness * point["UL"] < point["signal"]
            really_not_excluded = point["UL"] > looseness * point["signal"]
            inside = curve.IsInside ( x,y )
            pts["total"]+=1
            s=""
            if excluded:
                s="excluded"
            else:
                s="not_excluded"
            if inside:
                s+="_inside"
            else:
                s+="_outside"
            pts[s]+=1
            if really_excluded and not inside:
                pts["wrong"]+=1
            if really_not_excluded and inside:
                pts["wrong"]+=1
        logger.debug ( "points in categories %s" % str(pts) )
        print ( "[validationObjs] points in categories %s" % str(pts) )
        if pts["total"]==0:
            return float("nan")
        return 1.0 - float(pts["wrong"]) / float(pts["total"])

    def setSLHAdir(self,slhadir):
        """
        Defines the folder or tar file containing all the slha files to be
        used to generate the validation plot

        :param slhadir: existing folder containing SLHA files
        """

        if not os.path.isdir(slhadir) and not os.path.isfile(slhadir):
            logger.error("SLHA files not found in %s for %s" %(slhadir,str(self)))
            sys.exit()
        else:
            self.slhaDir = slhadir

    def getOfficialCurve(self):
        """
        Reads the root file associated to the ExpRes and
        obtain the experimental exclusion curve for the corresponding TxName and Axes.
        Saves the exclusion curve in self.officialCurve

        :return: a root TGraph object
        """
        tgraphDict = getExclusionCurvesFor(self.expRes,txname=self.txname,axes=self.axes)
        if not tgraphDict: return None
        tgraph = tgraphDict[self.txname]
        if len(tgraph) > 1:
            logger.warning("More than one exclusion curve found. Using the first one.")

        return tgraph[0]

    def getData(self):
        """
        Runs SModelS on the SLHA files listed in slhaDir and
        returns the list of excluded and allowed points.
        """

        self.data = runSModelSFor(self)
        #Apply k-factors to theory prediction (default is 1)
        for ipt,pt in enumerate(self.data):
            pt['signal'] *= self.kfactor 
            self.data[ipt] = pt

    def getPlot(self,silentMode=True):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurve to generate the exclusion plot
        :param silentMode: If True the plot will not be shown on the screen
        """

        self.plot,self.base = createPlot(self,silentMode)

    def savePlot(self,validationDir=None):
        """
        Saves the plot in .png format in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder

        :param validationDir: Folder where the plot will be saved
        """


        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False

        if not validationDir:
            vDir = os.path.join(self.expRes.path,'validation')
        else: vDir = validationDir

        if not os.path.isdir(vDir):
            logger.info("Creating validation folder "+vDir)
            os.mkdir(vDir)

        filename = self.plot.GetTitle()+'.png'
        filename = filename.replace(self.expRes.getValuesFor('id')+"_","")
        filename = os.path.join(vDir,filename)
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","")
        self.plot.Print(filename)
        return True

    def saveData(self,validationDir=None,datafile=None):
        """
        Saves the data and plot in a text file in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder
        If datafile is not define, uses the default naming (Txname_axes.py)

        :param validationDir: Folder where the root file will be saved
        :param datafile: Name of the data file
        """

        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False
        if not hasattr(self,'data') or not self.data:
            logger.warning("No data found. Nothing will be saved")
            return False

        if not validationDir:
            validationDir = os.path.join(self.expRes.path,'validation')

        if not os.path.isdir(validationDir):
            logger.info("Creating validation folder "+validationDir)
            os.mkdir(validationDir)

        if not datafile:
            datafile = self.plot.GetTitle()+'.py'
            datafile = datafile.replace(self.expRes.getValuesFor('id')+"_","")
            datafile = os.path.join(validationDir,datafile)
            datafile = datafile.replace("*","").replace(",","").replace("(","").replace(")","")


        #Save data to file
        f = open(datafile,'w')
        dataStr = str(self.data)
        dataStr = dataStr.replace('[fb]','*fb').replace('[pb]','*pb')
        dataStr = dataStr.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
        f.write("validationData = "+dataStr)
        f.close()

        return True






