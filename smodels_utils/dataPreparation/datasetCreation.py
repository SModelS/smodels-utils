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

    def __init__( self, fname_obs, fname_bg, hname_obs, hname_bg ):
        """
        :param fname_obs: filename for root file with n_obs for datasets
        :param fname_bg: filename for root file with bg estimates for datasets
        :param hname_obs: histogram name of n_obs, in fname_obs
        :param hname_bg: histogram name for bg estimates
        """
        self.file_obs = ROOT.TFile ( fname_obs )
        self.file_bg = ROOT.TFile ( fname_bg )
        self.histo_obs = self.file_obs.Get ( hname_obs )
        self.histo_bg = self.file_bg.Get ( hname_bg )
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
        name = self.xaxis.GetBinLabel ( self.counter )
        nobs = self.histo_obs.GetBinContent ( self.counter )
        bg = self.histo_bg.GetBinContent ( self.counter )
        bgerr = self.histo_bg.GetBinError ( self.counter )
        dataset = DataSetInput ( name )
        dataset.setInfo ( dataType="efficiencyMap", dataId = name, observedN = nobs,
                expectedBG=bg, bgError=bgerr )
        return dataset

creator = DatasetCreator ( "CMS-SUS-16-033_Figure_009.root", \
    "PostFitHistograms.root", "DataObs", "PostFitTotal" )
for c in creator:
    print ( c )
