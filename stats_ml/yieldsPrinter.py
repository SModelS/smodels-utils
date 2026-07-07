#!/usr/bin/env python3

"""
.. module:: yieldPrinter
   :synopsis: a printer that prints the signal yields
   of predictions into json files. Mostly for debugging
   ML models.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os
from typing import Optional
from smodels.matching.theoryPrediction import TheoryPredictionList
from smodels.tools.printers.basicPrinter import BasicPrinter
from smodels.base.smodelsLogging import logger

import sys
sys.path.insert(0,".")
from .yieldsWriter import yieldsToDicts, generalInfo

class YieldsPrinter(BasicPrinter):
    """ Printer class exclusively to print signal yields 
    into a yield*.json file """
    def __init__( self, output : str = 'yields.json', 
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
        self.filename = f'{filename}.json'
        if overwrite and os.path.isfile(self.filename):
            newfilename = self.filename.replace(".json",".json.old")
            if not silent:
                # logger.warning( f"removing output file {self.filename}" )
                logger.warning( f"moving old output file {self.filename} to {newfilename}" )
            shutil.move ( self.filename, newfilename )
            # os.remove(self.filename)
        logger.info ( f"we set output file to {self.filename}" )

    def flush ( self ):
        logger.info ( f"writing yields to {self.filename}" )
        import json, copy
        all_dicts = {}
        oldGInfo = None
        mus = [ 0., .001, .2, .4, 1., 2., 5., 100. ]
        for tp in self.toPrint:
            gInfo = generalInfo ( tp )
            gInfo["mus"] = mus
            if oldGInfo == None:
                all_dicts["general_info"] = gInfo
            elif oldGInfo != gInfo:
                logger.error ( f"general info changed: {gInfo} != {oldGInfo}" )
            dicts = yieldsToDicts ( tp )
            all_dicts[tp.dataset.globalInfo.id] = dicts
            oldGInfo = copy.deepcopy ( gInfo )
        with open ( self.filename, "wt" ) as f:
            d = json.dumps ( all_dicts, indent=4 )
            f.write ( d )
            f.close()

    def addObj(self,obj):
        if type(obj) != TheoryPredictionList:
            return
        logger.info ( f"adding {type(obj).__name__}" )
        for tp in obj:
            logger.info ( f"adding {tp.dataset.globalInfo.id}" )
            self.toPrint.append( tp )

from smodels.tools.printers.printerRegistry import PrinterRegistry
PrinterRegistry.register ( YieldsPrinter, "yields" )
