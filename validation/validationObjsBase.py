#!/usr/bin/env python3

"""
.. module:: validationObjsBase
   :synopsis: Base class for ValidationPlot and GraphsValidationPlot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import logging
import os
from validationHelpers import getDefaultModel

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.ERROR)

class ValidationObjsBase():
    """
    The base class for ValidationPlot and GraphsValidationPlot, as they share much
    of their code.
    """

    def getParameterFile(self,tempdir : str = None ) -> str:
        """
        Creates a temporary parameter file to be passed to runSModelS

        :param tempdir: Temporary folder where the parameter file will be created. Default = current folder.
        """

        #Get the analysis ID, txname and dataset ID:
        expId = self.expRes.globalInfo.id
        txname = self.expRes.getTxNames()[0].txName

        #Get number of cpus:
        if not hasattr(self, 'ncpus') or not self.ncpus:
            self.ncpus  = 1
            if "ncpus" in self.options:
                self.ncpus = self.options["ncpus"]

        if tempdir is None: tempdir = os.getcwd()
        parFile = os.path.join ( tempdir, "parameter.ini" )
        if os.path.exists ( parFile ):
            if self.options['generateData']==None:
                logger.warning ( f"parameter file {parFile} exists already, but generateData is ondemand. Will use." )
            else:
                logger.warning ( f"weird, parameter file {parFile} already exists?" )
                parFile = tempfile.mktemp(dir=tempdir,prefix='parameter_',suffix='.ini' ) # , text=True )
        pf = open ( parFile, "wt" )

        combine = "False"
        if self.combine:
            combine = "True"
            self.validationType="combine"
        model = self.options["model"]
        if model == "default":
            model = getDefaultModel ( tempdir )
        with open ( parFile, "w" ) as f:
            f.write("[options]\ninputType = SLHA\ncheckInput = True\ndoInvisible = True\ndoCompress = True\ncomputeStatistics = True\ntestCoverage = False\n" )
            f.write ( f"combineSRs = {combine}\n" )
            f.write ( f"pyhfbackend = pytorch\n" )
            if self.options["keepTopNSRs"] not in  [ None, 0 ]:
                f.write ( "reportAllSRs = True\n" )
            sigmacut = 0.000000001
            minmassgap = 2.0
            maxcond = 1.0
            promptWidth=1.1
            if "sigmacut" in self.options:
                sigmacut = self.options["sigmacut"]
            if "minmassgap" in self.options:
                minmassgap = self.options["minmassgap"]
            if "maxcond" in self.options:
                maxcond = self.options["maxcond"]
            if "promptWidth" in self.options:
                promptWidth = self.options["promptWidth"]
            dataselector = "all"
            if len(self.expRes.datasets)>1:
                dataselector = "efficiencyMap"
            f.write(f"[experimentalFeatures]\n" )
            useTevatron = False
            if "useTevatronCLsConstruction" in self.options:
                useTevatron = self.options["useTevatronCLsConstruction"]
            f.write ( f"tevatroncls = {useTevatron}\n" )
            f.write(f"[parameters]\nsigmacut = {sigmacut}\nminmassgap = {minmassgap}\nmaxcond = {maxcond}\nncpus = {self.ncpus}\n" )
            f.write(f"[database]\npath = {self.databasePath}\nanalyses = {expId}\ntxnames = {txname}\ndataselector = {dataselector}\n" )
            f.write("[printer]\noutputFormat = version2\noutputType = python\n")
            f.write(f"[particles]\n")
            if not "share.models" in model:
                model = f"share.models.{model}"
            f.write(f"model={model}\n" )
            f.write(f"promptWidth={promptWidth}\n" )
            #expected = "posteriori"
            #expected = "priori"
            expected = self.options["expectationType"]
            f.write( f"[python-printer]\naddElementList = False\ntypeOfExpectedValues='{expected}'\nprinttimespent=True\n")
            f.close()
        # os.close(pf)
        pf.close()
        return parFile
