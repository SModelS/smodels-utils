#!/usr/bin/env python3

"""
.. module:: datasetCreation
   :synopsis: A facility to create a number of datasets from e.g. root files.
              Should be used for analyses with large number of datasets and
              covariance matrix. Made to work with CMS-SUS-16-033.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import math
import copy
import sys
import ROOT
sys.path.insert ( 0, "../../../smodels" )
sys.path.insert ( 0, "../.." )
from smodels.tools.smodelsLogging import logger
from smodels.tools.SimplifiedLikelihoods import Model, UpperLimitComputer
from smodels.tools.physicsUnits import fb, pb
from smodels_utils.dataPreparation.inputObjects import MetaInfoInput,DataSetInput
from smodels_utils.dataPreparation.databaseCreation import databaseCreator
class DatasetsFromLatex:
    """
    class that produces the datasets from LateX table
    """
    def __init__( self, texfile, max_datasets=None, c_obs=5, c_bg=6, ds_name="sr#0",
                  aggregate = None ):
        """
        :param texfile: file to parse
        :param max_datasets: consider a maximum of n datasets
        :param c_obs: number of column with observed events
        :param c_bg: number of column with expected bg events and errors
        :param ds_name: name of datasets, using #n as placeholders for value of
                        nth column. If ds_name is an integer, interpret it as
                        column number.
        :param aggregate: aggregate signal regions, given by indices, e.g.
         [[0,1,2],[3,4]] or signal region names, e.g.[["sr0","sr1"],["sr2"]].
        """
        self.texfile = texfile
        self.max_datasets = max_datasets
        self.c_obs = c_obs
        self.c_bg = c_bg
        self.ds_name = ds_name
        self.aggregate = aggregate
        self.counter = 0
        self.datasetOrder = []
        self.create()
        databaseCreator.datasetCreator = self
    
    def create ( self ):
        f = open ( self.texfile )
        self.lines = f.readlines()
        f.close()
        self.createAllDatasets()

    def setDataSetOrder ( self, info ):
        """ set the datasetOrder for the covariance matrix.
            'info' is the MetaInfoInput object. """
        info.datasetOrder = ",". join ( self.datasetOrder )

    def __iter__ ( self ):
        return self

    def next ( self ): ## for python2
        return self.__next__()

    def clean ( self, line ):
        line = line.replace ( "\\hline", "" )
        line = line.replace ( "\\\\", "" )
        line = line.strip()
        return line

    def getBGAndError ( self, sbg ):
        if "\\pm" in sbg:
            tokens = sbg.split ( "\\pm" )
            bg = float ( tokens[0].replace("$","" ) )
            bgerr = float ( tokens[1].replace("$","" ) )
            return bg,bgerr
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
        tot_errs = [ math.sqrt ( stat_errs[i]**2 + sys_errs[i]**2  ) for i in range(2) ]
        bgerr = max ( tot_errs )
        return bg,bgerr

    def createAllDatasets ( self ):
        """ create all datasets in a single go. makes aggregation easier. """
        logger.info ( "now creating all datasets" )
        self.datasets = []
        counter=0
        for l in self.lines:
            line = self.clean ( l )
            if line == "":
                continue
            tokens = line.split ( "&" )
            binnr = counter
            try:
                binnr = int ( tokens[0] )
            except Exception as e:
                pass
            nobs = int ( tokens[self.c_obs] )
            sbg = tokens[self.c_bg].strip()
            bg, bgerr = self.getBGAndError ( sbg )
            name = "sr%d" % binnr 
            dataId = self.ds_name
            for i,token in enumerate ( tokens ):
                ctoken = token.strip()
                ctoken = ctoken.replace ( "-", "_" )
                dataId = dataId.replace ( "#%d" % i, ctoken )
            dataset = DataSetInput ( name )
            dataset.setInfo ( dataType="efficiencyMap", dataId = dataId, observedN = nobs,
                expectedBG=bg, bgError=bgerr )
            counter+=1
            self.datasetOrder.append ( '"%s"' % dataId )
            self.datasets.append ( dataset )
        if self.aggregate != None:
            self.aggregateDSs()

    def aggregateToOne ( self, ctr, agg ):
        """ aggregate one list to a single dataset. """
        newds = copy.deepcopy ( self.origDataSets[ agg[0] ] )
        newds._name = "ar%d" % ctr
        aggregated = ""
        observedN, expectedBG, bgError2 = 0, 0., 0.
        for a in agg:
            ds = self.origDataSets[ a ]
            observedN += ds.observedN
            expectedBG += ds.expectedBG
            bgError2 += ds.bgError**2 ## FIXME this comes from the cov mat
            aggregated += ds.dataId + "+"
        newds.observedN = observedN
        newds.expectedBG = expectedBG
        oldBgError = math.sqrt ( bgError2 )
        bgErr2 = eval(databaseCreator.metaInfo.covariance)[ctr][ctr]
        newds.bgError = math.sqrt ( bgErr2 )
        if abs ( oldBgError - newds.bgError ) / newds.bgError > .2:
            logger.info ( "directly computed error and error from covariance vary greatly.!" )
        ntoys, alpha = 50000, .05
        lumi = eval ( databaseCreator.metaInfo.lumi )
        comp = UpperLimitComputer ( lumi, ntoys, 1. - alpha )
        m = Model ( newds.observedN, newds.expectedBG, bgErr2, None, 1. )
        ul = comp.ulSigma ( m, marginalize=True ).asNumber ( fb )
        newds.upperLimit = str("%f*fb" % ul )
        ule = comp.ulSigma ( m, marginalize=True, expected=True ).asNumber ( fb )
        newds.expectedUpperLimit =  str("%f*fb" % ule ) 
        newds.aggregated = aggregated[:-2]
        newds.dataId = "ar%d" % ctr ## for now the dataset id is the agg region id
        return newds
                
    def aggregateDSs ( self ):
        """ now that the datasets are created, aggregate them. """
        self.origDatasetOrder = copy.deepcopy ( self.datasetOrder )
        self.origDataSets = copy.deepcopy ( self.datasets )
        dsorder = [ '"ar%d"' % x for x in range(len(self.aggregate)) ]
        self.datasetOrder = dsorder
        self.datasets = [] ## rebuild
        for ctr,agg in enumerate(self.aggregate):
            self.datasets.append (self.aggregateToOne ( ctr, agg ) )
        databaseCreator.clear() ## reset list in databasecreator
        for i in self.datasets:
            databaseCreator.addDataset ( i )
        logger.info ( "Aggregated %d to %d datasets" % ( len(self.origDataSets), len(self.datasets) ) )

    def __next__ ( self ):
        """ return next dataset. """
        if self.max_datasets and self.counter >= self.max_datasets:
            # we are told not to produce more
            raise StopIteration()
        if len(self.datasets)==0:
            raise StopIteration()
        self.counter+=1
        nxt = self.datasets.pop(0)
        return nxt
            
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
        databaseCreator.datasetCreator = self

    def setDataSetOrder ( self, info ):
        """ set the datasetOrder for the covariance matrix.
            'info' is the MetaInfoInput object. """
        info.datasetOrder = "FIXME: DatasetsFromRoot.setDataSetOrder not implemented"

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
