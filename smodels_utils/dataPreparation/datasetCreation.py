#!/usr/bin/env python3

"""
.. module:: datasetCreation
   :synopsis: A facility to create a number of datasets from e.g. root files.
              Should be used for analyses with large number of datasets and
              covariance matrix. Made to work with CMS-SUS-16-033.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
import ROOT
sys.path.insert ( 0, "../../../smodels" )
sys.path.insert ( 0, "../.." )
from smodels.tools.smodelsLogging import logger
from smodels.tools.statistics import upperLimit
from smodels_utils.dataPreparation.inputObjects import MetaInfoInput,DataSetInput

class DatasetCreator:
    """
    class that produces the datasets
    """

    def __init__( self, observed_histo, bg_histo, readDatasetNames=True ):
        """
        :param observed_histo: filename and histogramname of observed event counts,
            filename and name of histo are separated with a ":".
        :param bg_histo: filename and histogramname of bg event counts,
            filename and name of histo are separated with a ":".
        :param readDatasetNames: try to retrieve dataset names from histogram
        """
        fname_obs, hname_obs = observed_histo.split(":")
        fname_bg, hname_bg = bg_histo.split(":")
        self.file_obs = ROOT.TFile ( fname_obs )
        self.file_bg = ROOT.TFile ( fname_bg )
        self.histo_obs = self.file_obs.Get ( hname_obs )
        self.histo_bg = self.file_bg.Get ( hname_bg )
        self.readDatasetNames = readDatasetNames
        if not self.histo_obs:
            logger.error ( "could not get histo ``%s'' file ``%s''" % \
                             ( hname_obs, fname_obs ) )
            sys.exit()
        self.create()

    def create ( self ):
        self.n = self.histo_obs.GetNbinsX()
        if self.histo_bg.GetNbinsX() != self.n:
            logger.error ( "number of datasets does not match between files." )
            sys.exit()
        self.counter = 0
        self.xaxis = self.histo_obs.GetXaxis()

    def __iter__ ( self ):
        return self

    def next ( self ): ## for python2
        return self.__next__()

    def __next__ ( self ):
        self.counter += 1
        if self.counter > self.n:
            raise StopIteration ()
        name = "sr%d" % self.counter
        if self.readDatasetNames:
            name = self.xaxis.GetBinLabel ( self.counter )
        nobs = self.histo_obs.GetBinContent ( self.counter )
        bg = self.histo_bg.GetBinContent ( self.counter )
        bgerr = self.histo_bg.GetBinError ( self.counter )
        dataset = DataSetInput ( name )
        dataset.setInfo ( dataType="efficiencyMap", dataId = name, observedN = nobs,
                expectedBG=bg, bgError=bgerr )
        return dataset

if __name__ == "__main__":
    creator = DatasetCreator ( "CMS-SUS-16-033_Figure_009.root:DataObs", \
                               "PostFitHistograms.root:PostFitTotal" )
    for c in creator:
        print ( c )
