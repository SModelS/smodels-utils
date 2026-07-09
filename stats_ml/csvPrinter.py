#!/usr/bin/env python3

"""
.. module:: csvPrinter
   :synopsis: a printer that prints the signal yields
   and nlls into csv files, for joaquin to used for training.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os, time, shutil
from typing import Optional
from smodels.matching.theoryPrediction import TheoryPredictionList
from smodels.tools.printers.basicPrinter import BasicPrinter
from smodels.base.smodelsLogging import logger

import sys
sys.path.insert(0,".")
from .yieldsWriter import yieldsToDicts, formatMu

class CsvPrinter(BasicPrinter):
    """ Printer class exclusively to print signal yields 
    into a yield*.csv file """
    def __init__( self, output : str = 'yields.csv', 
                  filename : Optional[os.PathLike]=None,
                  outputFormat : str = 'version3' ):
        BasicPrinter.__init__(self, output, filename, outputFormat)
        self.toPrint = []

    def setOutPutFile( self, filename : os.PathLike, overwrite : bool = True, 
                       silent : bool = False ):
        """
        Set the basename for the text printer. The output filename will be

        filename.py.
        :param filename: Base filename
        :param overwrite: If True and the file already exists, it will be removed.
        :param silent: dont comment removing old files
        """

        filename = filename.replace(".slha","")
        self.filename = f'{filename}.csv'
        if overwrite and os.path.isfile(self.filename):
            newfilename = self.filename.replace(".csv",".csv.old")
            if not silent:
                # logger.warning( f"removing output file {self.filename}" )
                logger.warning( f"moving old output file {self.filename} to {newfilename}" )
            shutil.move ( self.filename, newfilename )
            # os.remove(self.filename)
        logger.info ( f"we set output file to {self.filename}" )

    def flush ( self ):
        """ write it all out """
        logger.info ( f"writing yields to {self.filename}" )
        import copy
        mus = [ 0., .001, .01, .05, .2, .4, 1., 2., 5., 20., 100. ]
        csvlines = []
        regions = []
        for tp in self.toPrint:
            anaId = tp.dataset.globalInfo.id
            if True and not "-orig" in anaId:
                continue
            dicts = yieldsToDicts ( tp, mus=mus, expected_also = True )
            nlls = dicts[0]
            for d in dicts[1:]:
                oldregions = regions[:]
                regions = [ k for k,v in d["nsignals"].items() ]
                if oldregions != []:
                    assert regions == oldregions, f"regions changed from {oldregions} to {regions}??"
                nll_0 = nlls[ "nll_mu0" ] 
                nllE_0 = nlls[ "nllE_mu0" ] 
                nllA_0 = nlls[ "nllA_mu0" ] 
                nllEA_0 = nlls[ "nllEA_mu0" ] 
                for mu in mus:
                    smu = formatMu ( mu )
                    yields = d[f"yields_mu{smu}"]
                    nll = nlls[ f"nll_mu{smu}" ]
                    nllE = nlls[ f"nllE_mu{smu}" ]
                    nllA = nlls[ f"nllA_mu{smu}" ]
                    nllEA = nlls[ f"nllEA_mu{smu}" ]
                    line = ",".join(map(str,yields))
                    line += f",{nllE_0},{nllE},{nll_0},{nll}"
                    line += f",{nllEA_0},{nllEA},{nllA_0},{nllA}"
                    csvlines.append ( line )
        regions += [ "nLL_exp_mu0", "nLL_exp_mu1", "nLL_obs_mu0", 
                     "nLL_obs_mu1", "nLLA_exp_mu0", "nLLA_exp_mu1", 
                     "nLLA_obs_mu0", "nLLA_obs_mu1" ]
        fline = ",".join(regions)
        with open ( self.filename, "wt" ) as f:
            f.write ( fline + "\n" )
            for line in csvlines:
                f.write ( line + "\n" )
                # print ( line )
            f.close()

    def addObj(self,obj):
        if type(obj) != TheoryPredictionList:
            return
        logger.info ( f"adding {type(obj).__name__}" )
        for tp in obj:
            logger.info ( f"adding {tp.dataset.globalInfo.id}" )
            self.toPrint.append( tp )

from smodels.tools.printers.printerRegistry import PrinterRegistry
PrinterRegistry.register ( CsvPrinter, "csv" )
