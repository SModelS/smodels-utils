#!/usr/bin/env python

"""
.. module:: covarianceHandler
   :synopsis: methods and classes around covariances

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
import copy
import logging
from smodels_utils.helper import prettyDescriptions

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)

def computeAggCov ( covariance, agg1, agg2 ):
    """ compute the covariance between agg1 and agg2
    :param covariance: the covariance matrix
    :param agg1: list of indices to aggregate
    :param agg2: list of indices to aggregate
    """
    C=0.
    for i in agg1:
        for j in agg2:
            C+=covariance[i-1][j-1]
    return C

def aggregateMe ( covariance, aggregate ):
    """ aggregate the covariance matrix according to aggregate
    :param covariance: the matrix.
    :param aggregate: list of lists of indices
    :returns a small covariance matrix, and a dataset order
    """
    newDSOrder=[]
    nNew = len(aggregate)
    row = [0.]*nNew
    newCov = []
    oldcov = copy.deepcopy ( covariance )
    for i in range(nNew):
        newCov.append ( copy.deepcopy(row) )
    #logger.error ( "aggregating cov matrix from %d to %d dims." % ( self.n,nNew) )
    for ctr,agg in enumerate ( aggregate ):
        newDSOrder.append ( "ar%d" % ctr )
        V=0.
        for i in agg:
            for j in agg:
                V+=covariance[i-1][j-1]
        newCov[ctr][ctr]=V
        for ctr2,agg2 in enumerate ( aggregate ):
            if ctr == ctr2: continue
            cov = computeAggCov ( covariance, agg, agg2 )
            newCov[ctr][ctr2]=cov
    return newCov, newDSOrder

class CovarianceHandler:
    def __init__ ( self, filename, histoname, max_datasets=None,
                   aggregate = None ):
        """ constructor.
        :param filename: filename of root file to retrieve covariance matrix
                         from.
        """
        import ROOT
        f=ROOT.TFile ( filename )
        h=self.getHistogram ( f, histoname )
        xaxis = h.GetXaxis()
        self.n=h.GetNbinsX()+1
        if max_datasets:
            self.n=min(max_datasets+1,self.n)
        self.datasetOrder = []
        self.covariance = []
        self.blinded_regions = []
        for i in range ( 1, self.n ):
            if i in self.blinded_regions:
                continue
            self.datasetOrder.append ( xaxis.GetBinLabel(i) )
            row = []
            for j in range ( 1, self.n ):
                if j in self.blinded_regions:
                    continue
                el = h.GetBinContent ( i, j )
                if i==j and el < 1e-4:
                   logger.error ( "variance in the covariance matrix at position %d has a very small (%g) value" % (i,el) )
                   logger.error ( "will set it to 1e-4" )
                   el = 1e-4
                row.append ( el )
            self.covariance.append ( row )

        if aggregate != None:
            ## aggregate the stuff
            self.aggregateThis ( aggregate )

        self.removeSmallValues()
        self.checkCovarianceMatrix()

    def checkCovarianceMatrix( self ):
        """ a quick check if the covariance matrix is invertible. """
        from smodels.tools.simplifiedLikelihoods import Data
        import scipy.linalg
        n=len(self.covariance)
        m=Data( [0.]*n, [0.]*n, self.covariance )
        logger.info ( "Check %d-dim covariance matrix for positive definiteness." % n )
        try:
            # I=(m.covariance)**(-1)
            I=scipy.linalg.inv(m.covariance)
        except Exception as e:
            logger.error ( "Inversion failed. %s" % e )
            sys.exit()
        try:
            from scipy import stats
            l=stats.multivariate_normal.logpdf([0.]*n,mean=[0.]*n,cov=m.covariance)
        except Exception as e:
            import numpy
            logger.error ( "computation of logpdf failed: %s" % e )
            logger.error ( "the first entries in the diagonal read:\n%s " % ( numpy.diag ( m.covariance )[:10] ) )
            sys.exit()

    def removeSmallValues ( self ):
        """ set small values in covariance matrix to zero """
        return
        #print ( "[CovarianceHandler] cov=",len(self.covariance), type(self.covariance),
        #        type(self.covariance[0][0]) )
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

    def aggregateThis ( self, aggregate ):
        """ yo. aggregate. """
        newCov, newDSOrder = aggregateMe ( self.covariance, aggregate )
        self.covariance = newCov
        self.datasetOrder=newDSOrder

    def getHistogram ( self, f, histoname ):
        """ simple method to retrieve histogram
        :param f: filehandle
        """
        h=f.Get ( histoname )
        if h: return h
        if not "/" in histoname:
            logger.error ( "cannot find %s in %s" % (histoname, f.GetName()))
            sys.exit()
        tokens = histoname.split("/")
        if not len(tokens)==2:
            logger.error ( "cannot interpret histoname %s in %s" % \
                            ( histoname, f.name ) )
            sys.exit()
        c= f.Get ( tokens[0] )
        if not c:
            logger.error ( "cannot retrieve %s from %s" % \
                            ( histoname, f.name ) )
            sys.exit()
        if c.ClassName() == "TCanvas":
            h=c.GetPrimitive ( tokens[1] )
            if h: return h
            logger.error ( "cannot retrieve %s from %s" % \
                            ( histoname, f.name ) )
            sys.exit()
        logger.error ( "cannot interpret %s in %s" % \
                        ( histoname, f.name ) )
        sys.exit()

