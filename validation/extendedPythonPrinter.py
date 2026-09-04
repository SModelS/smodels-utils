"""
.. module:: extendedPythonPrinter
   :synopsis: pythonPrinter like in smodels but with extra nlls

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
import os
from smodels.decomposition.topologyDict import TopologyDict
from smodels.matching.theoryPrediction import TheoryPredictionList,TheoryPrediction,TheoryPredictionsCombiner
from smodels.tools.ioObjects import OutputStatus
from smodels.tools.coverage import Uncovered
from smodels.base.physicsUnits import GeV, fb, TeV
from smodels.base.smodelsLogging import logger
from smodels.tools.printers.pythonPrinter import PyPrinter
from smodels.tools.printerTools import formatNestedDict
from smodels.statistics.basicStats import observed, apriori
from collections import OrderedDict
from typing import Optional
import unum
import time
from smodels.base.types import PathType

class ExtendedPyPrinter(PyPrinter):

    def __init__(self, output : str= 'stdout',
            filename : Optional[PathType]=None,
            outputFormat : str = 'version3'):
        PyPrinter.__init__(self, output, filename, outputFormat)

    def _formatTheoryPredictionList(self, obj: object) -> dict:
        """
        Format data of the TheoryPredictionList object.

        :param obj: A TheoryPredictionList object to be printed.
        """
        ExptRes = super()._formatTheoryPredictionList ( obj )["ExptRes"]
        tps = {}
        for tp in obj._theoryPredictions:
            did = f"{tp.expResult.globalInfo.id}:{tp.dataId()}:{tp.dataType()}"
            tps[did] = tp
        newDicts = []
        for resDict in ExptRes:
            dtid = resDict["DataSetID"]
            aid = resDict["AnalysisID"]
            dt = resDict["dataType"]
            did = f"{aid}:{dtid}:{dt}"
            if not did in tps:
                print ( f"[extendedPythonPrinter] {did} not in tps??" )
                sys.exit()
            tp = tps[did]
            
            nllE = tp.nll ( evaluationType = apriori )
            resDict['nllE'] = self._round( nllE )
            nllA = tp.nll ( asimov = 0 )
            resDict['nllA'] = self._round( nllA )
            nllEA = tp.nll ( evaluationType = apriori,
                asimov = 0 )
            resDict['nllEA'] = self._round( nllEA )
            newDicts.append ( resDict )

        return {'ExptRes': newDicts }

    def _formatTheoryPredictionsCombiner(self, obj: object) -> dict:
        """
        Format data of the TheoryPredictionsCombiner object.

        :param obj: A TheoryPredictionsCombiner object to be printed.
        """
        t = super()._formatTheoryPredictionsCombiner ( obj )
        resDict = t["CombinedRes"][0]

        nllE = obj.nll ( evaluationType = apriori )
        resDict['nllE'] = self._round( nllE )
        nllA = obj.nll ( asimov = 0 )
        resDict['nllA'] = self._round( nllA )
        nllEA = obj.nll ( evaluationType = apriori,
                asimov = 0 )
        resDict['nllEA'] = self._round( nllEA )

        if self.errorsforr:
            self.addErrorsForRValues ( obj, resDict )
        combRes = [ resDict ]
        return {'CombinedRes': combRes}

from smodels.tools.printers.printerRegistry import PrinterRegistry
## these two lines shouldnt be necessary, fix in 321
if "python" in PrinterRegistry.printers:
    PrinterRegistry.printers.pop ( "python" )
PrinterRegistry.register ( ExtendedPyPrinter, "python" )
