#!/usr/bin/env python3

"""
.. module:: datasetCreation
   :synopsis: A facility to create a number of datasets from e.g. root files.
              Should be used for analyses with large number of datasets and
              covariance matrix. Made to work with CMS-SUS-16-033.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging, sys
import ROOT
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.ERROR)


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

    def __iter__ ( self ):
        self.counter += 1
        if self.counter == self.n:
            raise Exception ( "end" )
        return self.counter

creator = DatasetCreator ( "CMS-SUS-16-033_Figure_009.root", \
    "PostFitHistograms.root", "DataObs", "PostFitTotal" )
for i in creator:
    print (i)
