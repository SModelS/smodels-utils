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
        logger.info ( f"writing yields to {self.filename}" )
        import copy
        mus = [ 0., .001, .2, .4, 1., 2., 5., 100. ]
        with open ( self.filename, "wt" ) as f:
            for tp in self.toPrint:
                dicts = yieldsToDicts ( tp, mus=mus, expected_also = True )
                nlls = dicts[0]
                for d in dicts[1:]:
                    print ( d )
                    for mu in mus:
                        smu = formatMu ( mu )
                        yields = d[f"yields_mu{smu}"]
                        nll = nlls[ f"nll_mu{smu}" ]
                        nllE = nlls[ f"nllE_mu{smu}" ]
                        nllA = nlls[ f"nllA_mu{smu}" ]
                        nllEA = nlls[ f"nllEA_mu{smu}" ]
                    line = ",".join(map(str,yields))
                    line += f",{nll},{nllE},{nllA},{nllEA}"
                    print ( line )
                # d = json.dumps ( all_dicts, indent=4 )
                # f.write ( d )
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
