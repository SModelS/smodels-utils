#!/usr/bin/env python3

"""
.. module:: datasetCreation
   :synopsis: A facility to create a number of datasets from e.g. root files.
              Should be used for analyses with large number of datasets and
              covariance matrix. Made to work with CMS-SUS-16-033.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import math
import sys
import ROOT
sys.path.insert ( 0, "../../../smodels" )
sys.path.insert ( 0, "../.." )
from smodels.tools.smodelsLogging import logger
from smodels.tools.statistics import upperLimit
from smodels_utils.dataPreparation.inputObjects import MetaInfoInput,DataSetInput

class DatasetsFromLatex:
    """
    class that produces the datasets from LateX table
    """
    def __init__ ( self, texfile, max_datasets=None, c_obs=5, c_bg=6, ds_name="sr#0" ):
        """
        :param texfile: file to parse
        :param max_datasets: consider a maximum of n datasets
        :param c_obs: number of column with observed events
        :param c_bg: number of column with expected bg events and errors
        :param ds_name: name of datasets, using #n as placeholders for value of nth column
        """
        self.texfile = texfile
        self.max_datasets = max_datasets
        self.c_obs = c_obs
        self.c_bg = c_bg
        self.ds_name = ds_name
        self.counter = 0
        self.create()
    
    def create ( self ):
        f = open ( self.texfile )
        self.lines = f.readlines()
        f.close()

    def __iter__ ( self ):
        return self

    def next ( self ): ## for python2
        return self.__next__()

    def clean ( self, line ):
        line = line.replace ( "\\hline", "" )
        line = line.replace ( "\\\\", "" )
        line = line.strip()
        return line

    def __next__ ( self ):
        if self.max_datasets and self.counter >= self.max_datasets:
            # we are told not to produce more
            raise StopIteration()
        try:
            line = ""
            while len(line)==0:
                line = self.clean ( self.lines.pop(0) )
        except IndexError as e:
            raise StopIteration()
        tokens = line.split ( "&" )
        binnr = int ( tokens[0] )
        nobs = int ( tokens[self.c_obs] )
        sbg = tokens[self.c_bg].strip()
        fst_sp = sbg.find(" " )
        bg = float ( sbg [ : fst_sp ] )
        sbgerrs = sbg[fst_sp:].strip()
        sbgerrs = sbgerrs.replace("- ","-" )
        errtokens = sbgerrs.split ( " " )
        cltokens = [ x.replace("$","").replace("^","").replace("{","").replace("}","").replace("_","").replace("+","") for x in errtokens ]
        ttokens = []
        for t in cltokens:
            if t!="":
                ttokens.append ( t )
        ## print ( "ttokens=",ttokens )
        stat_errs = list ( map ( float, ttokens[:2] ) )
        sys_errs = list ( map ( float, ttokens[2:] ) )
        #stat_errs = list ( map ( float, cltokens[0].split("-") ) )
        #sys_errs = list ( map ( float, cltokens[1].split("-") ) )
        tot_errs = [ math.sqrt ( stat_errs[i]**2 + sys_errs[i]**2  ) for i in range(2) ]
        bgerr = max ( tot_errs )
        name = "sr%d" % binnr 
        dataId = self.ds_name
        for i,token in enumerate ( tokens ):
            ctoken = token.strip()
            ctoken = ctoken.replace ( "-", "_" )
            dataId = dataId.replace ( "#%d" % i, ctoken )
        dataset = DataSetInput ( name )
        dataset.setInfo ( dataType="efficiencyMap", dataId = dataId, observedN = nobs,
            expectedBG=bg, bgError=bgerr )
        self.counter += 1
        return dataset
            
class DatasetsFromRoot:
    """
    class that produces the datasets from root files.
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
    creator = DatasetsFromRoot ( "CMS-SUS-16-033_Figure_009.root:DataObs", \
                               "PostFitHistograms.root:PostFitTotal" )
    for c in creator:
        print ( c )
