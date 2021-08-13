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
import re
import ROOT
sys.path.insert ( 0, "../../../smodels" )
sys.path.insert ( 0, "../.." )
from smodels.tools.smodelsLogging import logger
from smodels.tools.simplifiedLikelihoods import Data, UpperLimitComputer
from smodels.tools.physicsUnits import fb, pb
from smodels_utils.dataPreparation.inputObjects import MetaInfoInput,DataSetInput
from smodels_utils.dataPreparation.databaseCreation import databaseCreator


def createAggregationList ( aggregationborders ):
    """
    Very simple helper function that creates the lists of lists of aggregate
    regions, given the "borders", e.g. aggregationborder=[3,6,8] results
    in [[0,1,2],[3,4,5],[6,7,8]]

    :param aggregationborder: the indices where to "break" the SRs and
    start a new aggregate region.

    :result: list of lists of aggregate regions
    """
    def R_ ( min, max ):
        return list(range(min,max))

    ret=[]
    last=1
    for i,a in enumerate(aggregationborders):
        if a==0:
            continue
        if a<last:
            logger.error ( "borders not given in descending order?")
            sys.exit()
        ret.append ( R_(last,a) )
        last=a
    return ret

def aggregateToOne ( origDataSets, covariance, aggidx, agg, lumi, aggprefix ):
    """ aggregate one list of datasets to a single dataset.
    :param origDataSets: the original DataSets, as a list
    :param covariance: covariance matrix
    :param aggidx: number of aggregate region
    :param lumi: luminosity, in fb^-1
    :param aggprefix: prefix to use for aggregate SRs, typically "ar"
    :returns: list of aggregated DataSets
    """
    newds = copy.deepcopy ( origDataSets[ agg[0]-1 ] )
    newds._name = "%s%d" % ( aggprefix, aggidx+1 )
    aggregated = ""
    observedN, expectedBG, bgError2 = 0, 0., 0.
    originalSRs = []
    for a in agg:
        ds = origDataSets[ (a-1) ]
        observedN += ds.observedN
        expectedBG += ds.expectedBG
        bgError2 += ds.bgError**2 ## F
        aggregated += ds.dataId + ";"
        originalSRs.append ( ds.dataId )
    newds.observedN = observedN
    newds.expectedBG = round ( expectedBG, 5 )
    oldBgError = round ( math.sqrt ( bgError2 ), 5 )
    bgErr2 = covariance[aggidx][aggidx]
    newds.bgError = round ( math.sqrt ( bgErr2 ), 5 )
    if ( oldBgError - newds.bgError ) / newds.bgError > .2:
        logger.error ( "directly computed error and error from covariance vary greatly for ar%d: %s != %s!" % ( aggidx+1, oldBgError, newds.bgError  ) )
        if oldBgError > newds.bgError:
            logger.error ( "since direct computation is more conservative, I will use that one." )
            newds.bgError = oldBgError
    ntoys, alpha = 200000, .05
    # lumi = eval ( databaseCreator.metaInfo.lumi )
    # comp = UpperLimitComputer ( lumi, ntoys, 1. - alpha )
    comp = UpperLimitComputer ( ntoys, 1. - alpha )
    m = Data ( newds.observedN, newds.expectedBG, bgErr2, None, 1. )
    try:
        ul = comp.ulSigma ( m, marginalize=False ) / lumi.asNumber ( 1./fb )
        #ul = comp.ulSigma ( m, marginalize=False ).asNumber ( fb )
    except Exception as e:
        print ( "Exception", e )
        print ( "observed:",newds.observedN )
        sys.exit()
    newds.upperLimit = str("%f*fb" % ul )
    # ule = comp.ulSigma ( m, marginalize=False, expected=True ).asNumber ( fb )
    ule = comp.ulSigma ( m, marginalize=False, expected=True ) / lumi.asNumber(1./fb)
    newds.expectedUpperLimit =  str("%f*fb" % ule )
    newds.aggregated = aggregated[:-1]
    newds.originalSRs = originalSRs
    newds.dataId = "%s%d" % (aggprefix, aggidx+1) ## for now the dataset id is the agg region id
    return newds

def aggregateDataSets ( aggregates, origDataSets, covariance, lumi, aggprefix="ar" ):
    """ aggregate the DataSets
    :param aggregates: the aggregates, list of lists of indices of SRs

    :returns: the aggregate datasets
    """
    if type(covariance)==str:
        covariance=eval(covariance)
    if type(lumi)==str:
        lumi=eval(lumi)
    datasets = []
    for ctr,agg in enumerate( aggregates ):
        myaggs = aggregateToOne ( origDataSets, covariance, ctr, agg, lumi, aggprefix )
        datasets.append ( myaggs )
    return datasets

def createAggregationOrder ( aggregate, aggprefix="ar" ):
    """ create the right string for the datasetOrder field in globalInfo
    :param aggprefix: prefix used for aggregate regions, e.g. "ar"
    """
    dsorder = [ '"%s%d"' % (aggprefix, x+1) for x in range(len(aggregate)) ]
    ret = ",".join(dsorder)
    return ret

class DatasetsFromLatex:
    """
    class that produces the datasets from LateX table
    """
    def __init__( self, texfile, max_datasets=None, c_obs=5, c_bg=6, ds_name="sr#0",
                  aggregate = None, aggprefix="ar" ):
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
        self.aggprefix = aggprefix
        self.max_datasets = max_datasets
        self.c_obs = c_obs
        self.c_bg = c_bg
        self.ds_name = ds_name
        self.aggregate = aggregate
        self.counter = 0 ## counter for regions that are written out
        self.datasetOrder = []
        self.blinded_regions = []
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
        info.datasetOrder = self.datasetOrder# ",". join ( self.datasetOrder )

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
        sbg = sbg.replace("$","" ).replace("{","").replace("}","")
        sbg = re.sub("\\\\pm\s*([.\d]*)",r"+\1 -\1",sbg) ## replace "\pm x" with "+x -x"
        sbg = sbg.replace("+"," ").replace("-"," ").replace("^", " " ).replace("_"," " ) ## remove dollars, brackets
        tokens = sbg.split ()
        tokens = list ( map ( float, tokens ) )
        bg=tokens[0]
        stat=max(tokens[1],tokens[2])
        syst=0.
        if len(tokens)>4:
            syst=max(tokens[3],tokens[4])
        bgerr=math.sqrt(stat**2+syst**2)
        #print ( "parsing in tex file: %s -> (bg,err)=%s,%s" % ( sbg, bg,bgerr) )
        return bg,bgerr

    def createAllDatasets ( self ):
        """ create all datasets in a single go. makes aggregation easier. """
        logger.debug ( "now creating all datasets" )
        # print ( "now creating all datasets" )
        self.datasets = []
        counter=0
        count_all = 0
        for l in self.lines:
            line = self.clean ( l )
            if line == "":
                continue
            tokens = line.split ( "&" )
            binnr = counter+1
            try:
                binnr = int ( tokens[0] )
            except Exception as e:
                pass
            nobs = int ( tokens[self.c_obs] )
            sbg = tokens[self.c_bg].strip()
            bg, bgerr = self.getBGAndError ( sbg )
            name = "SR%d" % (binnr+1)
            # name = "sr%d" % (binnr)
            dataId = self.ds_name
            for i,token in enumerate ( tokens ):
                ctoken = token.strip()
                ctoken = ctoken.replace ( "-", "_" )
                dataId = dataId.replace ( "#%d" % i, ctoken )
            dataId = dataId.replace("$\\geq$",">=" )
            count_all+=1
            if not count_all in self.blinded_regions:
                counter+=1
                dataset = DataSetInput ( name )
                dataset.setInfo ( dataType="efficiencyMap", dataId = dataId, observedN = nobs,
                expectedBG=bg, bgError=bgerr )
                self.datasetOrder.append ( '"%s"' % dataId )
                self.datasets.append ( dataset )
        if self.aggregate != None:
            self.aggregateDSs()

    def aggregateDSs ( self ):
        """ now that the datasets are created, aggregate them. """
        self.origDatasetOrder = copy.deepcopy ( self.datasetOrder )
        self.origDataSets = copy.deepcopy ( self.datasets )
        self.datasetOrder = createAggregationOrder ( self.aggregate, self.aggprefix )
        self.datasets = aggregateDataSets ( self.aggregate, self.origDataSets, \
                databaseCreator.metaInfo.covariance, databaseCreator.metaInfo.lumi,
                self.aggprefix )
        #self.datasets = [] ## rebuild
        #for ctr,agg in enumerate(self.aggregate):
        #    myaggs = aggregateToOne ( self.origDataSets, eval(databaseCreator.metaInfo.covariance), ctr, agg, eval ( databaseCreator.metaInfo.lumi ) )
        #    self.datasets.append ( myaggs )
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
        name = "SR%d" % ( self.counter+1 )
        # name = "sr%d" % ( self.counter )
        if self.readDatasetNames:
            name = self.xaxis.GetBinLabel ( self.counter )
        nobs = self.histo_obs.GetBinContent ( self.counter )
        bg = self.histo_bg.GetBinContent ( self.counter )
        bgerr = self.histo_bg.GetBinError ( self.counter )
        dataset = DataSetInput ( name )
        dataset.setInfo ( dataType="efficiencyMap", dataId = name, observedN = nobs,
                expectedBG=bg, bgError=bgerr )
        return dataset

class DatasetsFromEmbaked:
    """
    class that produces the datasets from embaked info
    """
    def __init__( self, statsfile="orig/statsEM.py", max_datasets=None, sr_prefix="SR",
                  aggregate = None, aggprefix="AR" ):
        """
        :param statsfile: file with all stats info
        :param max_datasets: consider a maximum of n datasets
        :param sr_prefix: prefix of "original" datasets
        :param aggregate: aggregate signal regions, given by indices, e.g.
         [[0,1],[2]] or signal region names, e.g.[["sr0","sr1"],["sr2"]].
        """
        self.statsfile = statsfile
        self.aggprefix = aggprefix
        self.max_datasets = max_datasets
        self.sr_prefix = sr_prefix
        self.aggregate = aggregate
        self.counter = 0 ## counter for regions that are written out
        self.datasetOrder = []
        self.blinded_regions = []
        self.create()
        databaseCreator.datasetCreator = self

    def create ( self ):
        f = open ( self.statsfile )
        self.stats = eval ( f.read() )
        f.close()
        self.createAllDatasets()

    def setDataSetOrder ( self, info ):
        """ set the datasetOrder for the covariance matrix.
            'info' is the MetaInfoInput object. """
        info.datasetOrder = self.datasetOrder# ",". join ( self.datasetOrder )

    def __iter__ ( self ):
        return self

    def next ( self ): ## for python2
        return self.__next__()

    def createAllDatasets ( self ):
        """ create all datasets in a single go. makes aggregation easier. """
        logger.debug ( "now creating all datasets" )
        count_all = 0
        counter=0
        # print ( "now creating all datasets" )
        self.datasets = []
        ctwarning = 0
        for key,values in self.stats.items():
            if not key.startswith ( self.sr_prefix ):
                if ctwarning < 2:
                    print ( f"[datasetCreation] skipping {key} -- region name does not begin with '{self.sr_prefix}'" )
                if ctwarning == 3:
                    print ( f"[datasetCreation] .... (skipping a few more)" )
                ctwarning+=1
                continue
            nobs = values["nobs"]
            sbg = values["nb"]
            bg, bgerr = values["nb"], values["deltanb"]
            name = key
            p1 = name.find("_")
            if p1 > 0:
                name = name[:p1]
            # name = "SR%d" % (binnr+1)
            # name = "sr%d" % (binnr)
            dataId = key 
            count_all+=1
            if not count_all in self.blinded_regions:
                counter+=1
                dataset = DataSetInput ( dataId )
                dataset.setInfo ( dataType="efficiencyMap", dataId = dataId, observedN = nobs,
                expectedBG=bg, bgError=bgerr )
                self.datasetOrder.append ( '"%s"' % dataId )
                self.datasets.append ( dataset )
        if self.aggregate != None:
            self.aggregateDSs()

    def aggregateDSs ( self ):
        """ now that the datasets are created, aggregate them. """
        self.origDatasetOrder = copy.deepcopy ( self.datasetOrder )
        self.origDataSets = copy.deepcopy ( self.datasets )
        self.datasetOrder = createAggregationOrder ( self.aggregate, self.aggprefix )
        self.datasets = aggregateDataSets ( self.aggregate, self.origDataSets, \
                databaseCreator.metaInfo.covariance, databaseCreator.metaInfo.lumi,
                self.aggprefix )
        #self.datasets = [] ## rebuild
        #for ctr,agg in enumerate(self.aggregate):
        #    myaggs = aggregateToOne ( self.origDataSets, eval(databaseCreator.metaInfo.covariance), ctr, agg, eval ( databaseCreator.metaInfo.lumi ) )
        #    self.datasets.append ( myaggs )
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


if __name__ == "__main__":
    creator = DatasetsFromRoot ( "CMS-SUS-16-033_Figure_009.root:DataObs", \
                               "PostFitHistograms.root:PostFitTotal" )
    for c in creator:
        print ( c )
