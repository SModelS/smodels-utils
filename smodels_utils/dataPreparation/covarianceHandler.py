#!/usr/bin/env python

"""
.. module:: covarianceHandler
   :synopsis: methods and classes around covariances

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
import copy
import logging
import numpy
from smodels_utils.helper import prettyDescriptions

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)

## if errors in individual datasets are larger than the variances in the cov matrix,
## overwrite with conservative estimate
overrideWithConservativeErrors = True

minVariance = 1e-4 ## the minimum value for variance

def computeAggCov ( covariance : list[list], agg1 : list, agg2 : list, 
        zeroIndexed : bool = False ) -> float:
    """ compute the covariance between agg1 and agg2
    :param covariance: the covariance matrix
    :param agg1: list of indices to aggregate
    :param agg2: list of indices to aggregate
    :param zeroIndexed: are indices given one-indexed or zero-indexed

    :returns: the covariance (float)
    """
    C=0.
    di = 0
    if not zeroIndexed:
        di = 1
    for i in agg1:
        for j in agg2:
            C+=covariance[i-di][j-di]
    return C

def aggregateMe ( covariance : list[list], aggregate : list, 
          aggprefix : str ="AR", zeroIndexed : bool = False ) -> tuple[list,list]:
    """ aggregate the covariance matrix according to aggregate
    :param covariance: the matrix.
    :param aggregate: list of lists of indices
    :param zeroIndexed: are indices given one-indexed or zero-indexed
    :returns a small covariance matrix, and a dataset order
    """
    newDSOrder=[]
    nNew = len(aggregate)
    row = [0.]*nNew
    newCov = []
    oldcov = copy.deepcopy ( covariance )
    for i in range(nNew):
        newCov.append ( copy.deepcopy(row) )
    newDSOrder = [ f"{aggprefix}{ctr}" for ctr in range(nNew) ]
    if aggprefix == "SR":
    #logger.error ( f"aggregating cov matrix from {self.n} to {nNew} dims." )
        newDSOrder = [ f"{aggprefix}{agg}{ctr}" for agg in aggregate ]
    if type(aggregate) == dict:
        newDSOrder = []
        tmp = []
        for k,v in aggregate.items():
            newDSOrder.append ( k )
            tmp.append ( v )
        aggregate = tmp

    di = 1
    if zeroIndexed:
        di = 0
    #logger.error ( f"aggregating cov matrix from {self.n} to {nNew} dims." )
    for ctr,agg in enumerate ( aggregate ):
        V=0.
        for i in agg:
            for j in agg:
                #V+=covariance[i-1][j-1]
                V+=oldcov[i-di][j-di]
        newCov[ctr][ctr]=V ## that should be the new main diagonal
        for ctr2,agg2 in enumerate ( aggregate ):
            if ctr == ctr2: continue
            cov = computeAggCov ( covariance, agg, agg2, zeroIndexed )
            newCov[ctr][ctr2]=cov
    return newCov, newDSOrder

class CovarianceHandler:
    """ generic covariance handler class, contains e.g. the aggregation code,
    and the interaction method.  will be inherited by the concrete covariance
    handlers """
    def interact ( self, stuff ):
        import IPython
        IPython.embed()
        sys.exit() 

    def checkCovarianceMatrix( self ):
        """ a quick check if the covariance matrix is invertible. """
        from smodels.statistics.simplifiedLikelihoods import Data
        import scipy.linalg
        n=len(self.covariance)
        m=Data( [0.]*n, [0.]*n, self.covariance )
        logger.info(f"Check {n}-dim covariance matrix for positive definiteness.")
        try:
            # I=(m.covariance)**(-1)
            I=scipy.linalg.inv(m.covariance)
        except Exception as e:
            logger.error ( f"Inversion failed. {e}" )
            sys.exit()
        try:
            from scipy import stats
            l=stats.multivariate_normal.logpdf([0.]*n,mean=[0.]*n,cov=m.covariance)
        except Exception as e:
            import numpy
            logger.error ( f"computation of logpdf failed: {e}" )
            logger.error ( f"the first entries in the diagonal read:\n{numpy.diag ( m.covariance )[:10]}" )
            sys.exit()

    def removeSmallValues ( self ):
        """ set small values in covariance matrix to zero """
        return
        threshold = .05
        removed, ntot = 0, 0
        for irow,row in enumerate ( self.covariance ):
            for icol,col in enumerate ( row ):
                if icol >= irow:
                    continue
                corr = abs ( col ) / math.sqrt(self.covariance[irow][irow]*self.covariance[icol][icol])
                ntot += 1
                if corr < threshold:
                    removed += 1
                    # print ( f"removing {corr:.3f} <= {threshold} at ({irow},{icol}). was: {self.covariance[irow][icol]:.3f}." )
                    self.covariance[irow][icol]=0.
                    self.covariance[icol][irow]=0.
        if removed > 0:
            logger.warning ( f"removed {removed}/{ntot} correlations below threshold of {threshold} from covariance matrix" )

    def aggregateThis ( self, aggregate, zeroIndexed : bool = False ):
        """ yo. aggregate.
        :param zeroIndexed: are indices given one-indexed or zero-indexed
        """
        newCov, newDSOrder = aggregateMe ( self.covariance, aggregate,
                                           self.aggprefix, zeroIndexed )
        self.covariance = newCov
        self.datasetOrder=newDSOrder

class UPROOTCovarianceHandler ( CovarianceHandler ):
    def __init__ ( self, filename, histoname, max_datasets=None,
                   aggregate = None, aggprefix = "ar", zeroIndexed : bool = False,
                   scaleCov : float = 1.0 ):
        """ constructor.
        :param filename: filename of root file to retrieve covariance matrix
        from.
        :param scaleCov: scale the covariances down ever so slightly, to be
        sure the determinant stay negative.
        """
        self.aggprefix = aggprefix
        import uproot
        f=uproot.open ( filename )
        h=self.getHistogram ( f, histoname )
        xaxis = h.axes[0]
        self.n=len(xaxis)
        if max_datasets:
            self.n=min(max_datasets+1,self.n+1)
        self.datasetOrder = []
        self.covariance = []
        self.blinded_regions = []
        cterr = 0
        # self.interact ( xaxis )
        for i in range ( self.n ):
            if i in self.blinded_regions:
                continue
            dsId = xaxis.labels()[i]
            try:
                dsId = f"SR{int(dsId)}"
            except Exception as e:
                cterr += 1
            self.datasetOrder.append ( dsId )
            row = []
            for j in range ( self.n ):
                if j in self.blinded_regions:
                    continue
                el = h.values()[i][j]
                if i==j and el < 1e-4:
                   logger.error ( f"variance in the covariance matrix at position {i} has a very small value ({el:g})" )
                   logger.error ( "will set it to 1e-4" )
                   el = 1e-4
                if i!=j and scaleCov != 1.0:
                    el = scaleCov * el ## slight downscale!
                row.append ( el )
            self.covariance.append ( row )

        self.fullcovariance = copy.deepcopy ( self.covariance )
        if aggregate != None:
            ## aggregate the stuff
            self.aggregateThis ( aggregate, zeroIndexed )

        self.removeSmallValues()
        self.checkCovarianceMatrix()

    def getHistogram ( self, f, histoname ):
        """ simple method to retrieve histogram
        :param f: filehandle
        """
        h=f.get ( histoname )
        if h: return h
        if not "/" in histoname:
            logger.error ( f"cannot find {histoname} in {f.parent.file_path}" )
            sys.exit()
        tokens = histoname.split("/")
        """
        if len(tokens)==1:
            return f.get(tokens[0])
        """
        if not len(tokens)==2:
            logger.error ( f"cannot interpret histoname {histoname} in {f.name}" )
            sys.exit()
        c= f.get ( tokens[0] )
        if not c:
            logger.error ( f"cannot retrieve {histoname} from {f.name}" )
            sys.exit()
        if c.classname == "TCanvas":
            logger.error ( "we cannot read tcanvas objects with uproot!" )
            sys.exit()
            h=c.GetPrimitive ( tokens[1] )
            if h: return h
            logger.error ( f"cannot retrieve {histoname} from {f.name}" )
            sys.exit()
        logger.error ( f"cannot interpret {histoname} in {f.name}" )
        sys.exit()

class PYROOTCovarianceHandler ( CovarianceHandler ):
    def __init__ ( self, filename, histoname, max_datasets=None,
                   aggregate = None, aggprefix = "ar" ):
        """ constructor.
        :param filename: filename of root file to retrieve covariance matrix
                         from.
        """
        logger.error ( "using pyroot covariance handler. you may want to switch to uproot" )
        self.aggprefix = aggprefix
        import ROOT
        f=ROOT.TFile ( filename )
        h=self.getHistogram ( f, histoname )
        xaxis = h.GetXaxis()
        self.n=h.GetNbinsX()
        if max_datasets:
            self.n=min(max_datasets+1,self.n+1)
        self.datasetOrder = []
        self.covariance = []
        self.blinded_regions = []
        cterr = 0
        for i in range ( 1, self.n+1 ):
            if i in self.blinded_regions:
                continue
            dsId = xaxis.GetBinLabel(i)
            try:
                dsId = f"SR{int(dsId)}"
            except Exception as e:
                cterr += 1
            self.datasetOrder.append ( dsId )
            row = []
            for j in range ( 1, self.n+1 ):
                if j in self.blinded_regions:
                    continue
                el = h.GetBinContent ( i, j )
                if i==j and el < 1e-4:
                    logger.error ( f"variance in the covariance matrix at position {i} has a very small ({el:.4g}) value: will set to {minVariance}" )
                    el = minVariance
                row.append ( el )
            self.covariance.append ( row )

        if aggregate != None:
            ## aggregate the stuff
            self.aggregateThis ( aggregate )

        self.removeSmallValues()
        self.checkCovarianceMatrix()

    def getHistogram ( self, f, histoname ):
        """ simple method to retrieve histogram
        :param f: filehandle
        """
        h=f.Get ( histoname )
        if h: return h
        if not "/" in histoname:
            logger.error ( f"cannot find {histoname} in {f.GetName()}" )
            sys.exit()
        tokens = histoname.split("/")
        if not len(tokens)==2:
            logger.error ( f"cannot interpret histoname {histoname} in {f.name}" )
            sys.exit()
        c= f.Get ( tokens[0] )
        if not c:
            logger.error ( f"cannot retrieve {histoname} from {f.name}" )
            sys.exit()
        if c.ClassName() == "TCanvas":
            h=c.GetPrimitive ( tokens[1] )
            if h: return h
            logger.error ( f"cannot retrieve {histoname} from {f.name}" )
            sys.exit()
        logger.error ( f"cannot interpret {histoname} in {f.name}" )
        sys.exit()

class CSVCovarianceHandler ( CovarianceHandler ):
    def __init__ ( self, filename, max_datasets=None,
                   aggregate = None, aggprefix = "ar" ):
        """ constructor.
        :param filename: filename of root file to retrieve covariance matrix
                         from.
        """
        self.aggprefix = aggprefix
        f=open(filename,"rt")
        lines = f.readlines()
        f.close()
        #self.n=-1
        #if max_datasets:
        #    self.n=min(max_datasets+1,self.n)
        self.datasetOrder = []
        self.covariance = []
        self.blinded_regions = []
        tuples = []

        nmax = -1
        for line in lines:
            p1 = line.find("#")
            if p1 > -1:
                line = line[:p1]
            line = line.strip()
            if len(line)==0:
                continue
            if "Bin" in line: # tables header
                continue
            tokens = line.split(",")
            x,y,z = int(float(tokens[0])), int(float(tokens[1])), float(tokens[2])
            if x > nmax:
                nmax = x
            entry = [x-1,y-1,z]
            tuples.append ( entry )
        self.n = len ( tuples )
        for i in range(nmax):
            self.datasetOrder.append ( f"SR{i+1}" )
        a = numpy.array ( [ [0.]*nmax ]*nmax, dtype=float )
        for t in tuples:
            a[t[0]][t[1]]=t[2]
        a = a.tolist()
        self.covariance = a

        if aggregate != None:
            ## aggregate the stuff
            self.aggregateThis ( aggregate )

        self.removeSmallValues()
        self.checkCovarianceMatrix()

    def getHistogram ( self, f, histoname ):
        """ simple method to retrieve histogram
        :param f: filehandle
        """
        h=f.Get ( histoname )
        if h: return h
        if not "/" in histoname:
            logger.error ( f"cannot find {histoname} in {f.GetName()}" )
            sys.exit()
        tokens = histoname.split("/")
        if not len(tokens)==2:
            logger.error ( f"cannot interpret histoname {histoname} in {f.name}" )
            sys.exit()
        c= f.Get ( tokens[0] )
        if not c:
            logger.error ( f"cannot retrieve {histoname} from {f.name}" )
            sys.exit()
        if c.ClassName() == "TCanvas":
            h=c.GetPrimitive ( tokens[1] )
            if h: return h
            logger.error ( f"cannot retrieve {histoname} from {f.name}" )
            sys.exit()
        logger.error ( f"cannot interpret {histoname} in {f.name}" )
        sys.exit()

class FakeCovarianceHandler ( CovarianceHandler ):
    """ a covariance handler that creates the covariances from statistics,
    setting correlations to zero (for now) """
    def __init__ ( self, stats, max_datasets=None,
                   aggregate = None, aggprefix = "ar" ):
        """ constructor.
        :param stats: a dictionary containing the SR statistics
        """
        if aggregate != None or max_datasets != None:
            print ( "FIXME need to implement this" )
            sys.exit()
        self.aggprefix = aggprefix
        self.datasetOrder = []
        cov = []
        n = len(stats.items())
        self.n = n
        for i,(name,values) in enumerate(stats.items()):
            self.datasetOrder.append ( name )
            row = [0.]*i + [ values["deltanb"]**2 ] + [0.]*(n-i-1)
            cov.append ( row )
        self.covariance = cov

        if aggregate != None:
            ## aggregate the stuff
            self.aggregateThis ( aggregate )

        self.removeSmallValues()
        self.checkCovarianceMatrix()
