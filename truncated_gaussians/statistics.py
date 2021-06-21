#!/usr/bin/env python3

"""
.. module:: statistics
   :synopsis: a module meant to collect various statistical algorithms. For now it only contains the procedure that computes an approximate Gaussian likelihood from an expected an observer upper limit. See https://arxiv.org/abs/1202.3415.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import sys, os
sys.path.append(os.path.abspath('./smodels'))
from scipy import stats, optimize
from smodels.tools.smodelsLogging import logger
from scipy.special import erf
import numpy as np
from smodels.tools import runtime


def likelihoodFromLimits( upperLimit, expectedUpperLimit, nsig, nll=False, underfluct="norm_0"):
    """ computes the likelihood from an expected and an observed upper limit.
    :param upperLimit: observed upper limit, as a yield (i.e. unitless)
    :param expectedUpperLimit: expected upper limit, also as a yield
    :param nSig: number of signal events
    :param nll: if True, return negative log likelihood
    :param underfluct: How to handle Unfderfluctuations, "norm_0" uses a gaussian with maximum at 0,
        "norm_neg" uses a gaussian with negative maximum, "exp" uses an exponential distribution,
        defaults to "norm_0"


    :returns: likelihood (float)
    """
    assert ( upperLimit > 0. )

    def getSigma ( ul, muhat = 0. ):
        """ get the standard deviation sigma, given
            an upper limit and a central value. assumes a truncated Gaussian likelihood """
        # the expected scale, eq 3.24 in arXiv:1202.3415
        return ( ul - muhat ) / 1.96

    def llhd ( nsig, mumax, sigma_exp, nll ):
        ## need to account for the truncation!
        ## first compute how many sigmas left of center is 0.
        Zprime = mumax / sigma_exp
        ## now compute the area of the truncated gaussian
        A = stats.norm.cdf(Zprime)
        if nll:
            return np.log(A ) - stats.norm.logpdf ( nsig, mumax, sigma_exp )
        return float ( stats.norm.pdf ( nsig, mumax, sigma_exp ) / A )

    # sigma_exp = expectedUpperLimit / 1.96 # the expected scale, eq 3.24 in arXiv:1202.3415
    sigma_exp = getSigma ( expectedUpperLimit ) # the expected scale, eq 3.24 in arXiv:1202.3415
    
    denominator = np.sqrt(2.) * sigma_exp
    
    def root_func ( x ): ## we want the root of this one
        return (erf((upperLimit-x)/denominator)+erf(x/denominator)) / ( 1. + erf(x/denominator)) - .95

    def find_neg_mumax(upperLimit, expectedUpperLimit, xa, xb):
        while root_func(xa)*root_func(xb) > 0:
            xa = 2*xa
            #logger.error (xa, root_func(xa), xb, root_func(xb))
        mumax = optimize.brentq(root_func, xa, xb, rtol=1e-03, xtol=1e-06 )
        return mumax
    
    def getLam (ul):
        """ get the scale for the exponential destribution that reproduces the upper limit"""
        return -np.log(0.05)/ul

    def llhdexponential ( nsig, lam, nll ):
        ## exponential distribution
        if nll:
            return float(lam*nsig - np.log(lam))
        return float (stats.expon.pdf(nsig, scale=1/lam))
        
    

    dr = 2. * ( upperLimit - expectedUpperLimit ) / ( expectedUpperLimit + upperLimit )
    if dr>runtime._drmax:
        if runtime._cap_likelihoods == False:
            logger.warn("asking for likelihood from limit but difference between oUL(%.2f) and eUL(%.2f) is too large (dr=%.2f>%.2f)" % ( upperLimit, expectedUpperLimit, dr, runtime._drmax ) )
            return None
        oldUL = upperLimit
        upperLimit = expectedUpperLimit * ( 2. + runtime._drmax ) / ( 2. - runtime._drmax )
        logger.warn("asking for likelihood from limit but difference between oUL(%.2f) and eUL(%.2f) is too large (dr=%.2f>%.2f). capping to %.2f." % \
                ( oldUL, expectedUpperLimit, dr, runtime._drmax, upperLimit ) )
        ## we are asked to cap likelihoods, so we set observed UL such that dr == drmax

    
    if upperLimit <= expectedUpperLimit:
        ## underfluctuation. 
        if underfluct == "norm_0":
            return llhd ( nsig, 0., sigma_exp, nll )
        elif underfluct == "norm_neg":
            xa = -expectedUpperLimit
            xb = 1
            mumax = find_neg_mumax(upperLimit, expectedUpperLimit, xa, xb)
            return llhd(nsig, mumax, sigma_exp, nll)
        elif underfluct == "exp":
            lam = getLam(upperLimit)
            return llhdexponential(nsig, lam, nll)
        else:
            logger.warn("underfluct not defined, choose one of norm_0, norm_neg and exp")

    
   
    fA = root_func ( 0. )
    fB = root_func ( max(upperLimit,expectedUpperLimit) )
    if np.sign(fA*fB) > 0.:
        ## the have the same sign
        logger.error ( "when computing likelihood: fA and fB have same sign")
        return None
    mumax = optimize.brentq ( root_func, 0., max(upperLimit, expectedUpperLimit),
                              rtol=1e-03, xtol=1e-06 )
    llhdexp = llhd ( nsig, mumax, sigma_exp, nll )
    return llhdexp

def rvsFromLimits( upperLimit, expectedUpperLimit, n=1 ):
    """
    Generates a sample of random variates, given expected and observed likelihoods.
    The likelihood is modelled as a truncated Gaussian.

    :param upperLimit: observed upper limit, as a yield (i.e. unitless)
    :param expectedUpperLimit: expected upper limit, also as a yield
    :param n: sample size

    :returns: sample of random variates
    """
    
    sigma_exp = expectedUpperLimit / 1.96 # the expected scale
    denominator = np.sqrt(2.) * sigma_exp
    def root_func ( x ): ## we want the root of this one
        return (erf((upperLimit-x)/denominator)+erf(x/denominator)) / ( 1. + erf(x/denominator)) - .95

    fA,fB = root_func ( 0. ), root_func ( max(upperLimit,expectedUpperLimit) )
    if np.sign(fA*fB) > 0.:
        ## the have the same sign
        logger.error ( "when computing likelihood for %s: fA and fB have same sign" % self.analysisId() )
        return None
    mumax = optimize.brentq ( root_func, 0., max(upperLimit, expectedUpperLimit), rtol=1e-03, xtol=1e-06 )
    ret = []
    while len(ret)<n:
        tmp = stats.norm.rvs ( mumax, sigma_exp )
        if tmp > 0.:
            ret.append ( tmp )
    return ret

def deltaChi2FromLlhd ( likelihood ):
    """ compute the delta chi2 value from a likelihood (convenience function) """
    if likelihood == 0.:
        return 1e10 ## a very high number is good
    elif likelihood is None:
        return None

    return -2. * np.log ( likelihood )

def chi2FromLimits ( likelihood, expectedUpperLimit ):
    """ compute the chi2 value from a likelihood (convenience function).
    """
    sigma_exp = expectedUpperLimit / 1.96 # the expected scale
    l0 = 2. * stats.norm.logpdf ( 0., 0., sigma_exp )
    l = deltaChi2FromLlhd(likelihood)
    if l is None:
        return None

    return  l + l0

def llhdFromLimits_moments ( upperLimit, expectedUpperLimit, nll=False, underfluct="norm_0"):
    """Compute the Expected Value, Variance, Skewness and Mode of normalized Likelihood that was computed with the Expected and observed Upper Limit.
    :param upperLimit: observed upper limit, as a yield (i.e. unitless)
    :param expectedUpperLimit: expected upper limit, also as a yield
    :param nSig: number of signal events
    :param nll: if True, return negative log likelihood
    :param underfluct: How to handle Unfderfluctuations, "norm_0" uses a gaussian with maximum at 0,
        "norm_neg" uses a gaussian with negative maximum, "exp" uses an exponential distribution,
        defaults to "norm_0"


    :returns: EV, Var, Skew and Mode of computed Likelihood as dict
    """
    assert ( upperLimit > 0. )

    def getSigma ( ul, muhat = 0. ):
        """ get the standard deviation sigma, given
            an upper limit and a central value. assumes a truncated Gaussian likelihood """
        # the expected scale, eq 3.24 in arXiv:1202.3415
        return ( ul - muhat ) / 1.96

    sigma_exp = getSigma ( expectedUpperLimit ) # the expected scale, eq 3.24 in arXiv:1202.3415
    
    denominator = np.sqrt(2.) * sigma_exp
    
    def root_func ( x ): ## we want the root of this one
        return (erf((upperLimit-x)/denominator)+erf(x/denominator)) / ( 1. + erf(x/denominator)) - .95

    def find_neg_mumax(upperLimit, expectedUpperLimit, xa, xb):
        while root_func(xa)*root_func(xb) > 0:
            xa = 2*xa
        mumax = optimize.brentq(root_func, xa, xb, rtol=1e-03, xtol=1e-06 )
        return mumax
    
    def getLam (ul):
        """ get the scale for the exponential destribution that reproduces the upper limit"""
        return -np.log(0.05)/ul

    def llhdexponential ( nsig, lam, nll ):
        ## exponential distribution
        if nll:
            return float(lam*nsig - np.log(lam))
        return float (stats.expon.pdf(nsig, scale=1/lam))

    def trunc_norm_moments(mumax, sigma):
        rho = np.exp(-mumax**2/(2*sigma**2)) / (np.sqrt(2*np.pi)*(1 - stats.norm.cdf(0,loc=mumax,scale=sigma)))
        h = -mumax/sigma

        ev = mumax +(sigma*rho)
        var = sigma**2*(1 + rho*h - rho**2)
        #skew = sigma**3 * rho* ( (rho-h)**2 + rho*(rho-h) - 1 )
        skew = rho * (2*rho**2 - 3*rho*h + h**2 -1) / (1 + h*rho - rho**2)**(3/2)
        #skew = sigma*rho*(ev**2 - var)
        if mumax<0:
            mod = 0.
        else:
            mod = mumax
        
        return ({"ev":ev, "var":var, "skew":skew, "mode":mod})
        
        
    def exp_moments(lam):
        ev = 1/lam
        var = 1/(lam)**2
        skew = 2
        mod = 0.
        return ({"ev":ev, "var":var, "skew":skew, "mode":mod})

        
    dr = 2. * ( upperLimit - expectedUpperLimit ) / ( expectedUpperLimit + upperLimit )
    if dr>runtime._drmax:
        if runtime._cap_likelihoods == False:
            logger.warn("asking for likelihood from limit but difference between oUL(%.2f) and eUL(%.2f) is too large (dr=%.2f>%.2f)" % ( upperLimit, expectedUpperLimit, dr, runtime._drmax ) )
            return None
        oldUL = upperLimit
        upperLimit = expectedUpperLimit * ( 2. + runtime._drmax ) / ( 2. - runtime._drmax )
        logger.warn("asking for likelihood from limit but difference between oUL(%.2f) and eUL(%.2f) is too large (dr=%.2f>%.2f). capping to %.2f." % \
                ( oldUL, expectedUpperLimit, dr, runtime._drmax, upperLimit ) )
        ## we are asked to cap likelihoods, so we set observed UL such that dr == drmax

    
    if upperLimit <= expectedUpperLimit:
        ## underfluctuation. 
        if underfluct == "norm_0":
            mumax = 0
            return trunc_norm_moments(mumax, sigma_exp)
        elif underfluct == "norm_neg":
            xa = -expectedUpperLimit
            xb = 1
            mumax = find_neg_mumax(upperLimit, expectedUpperLimit, xa, xb)
            return trunc_norm_moments(mumax, sigma_exp)
        elif underfluct == "exp":
            lam = getLam(upperLimit)
            return exp_moments(lam)
        else:
            logger.warn("underfluct not defined, choose one of norm_0, norm_neg and exp")

    
   
    fA = root_func ( 0. )
    fB = root_func ( max(upperLimit,expectedUpperLimit) )
    if np.sign(fA*fB) > 0.:
        ## the have the same sign
        logger.error ( "when computing likelihood: fA and fB have same sign")
        return None
    mumax = optimize.brentq ( root_func, 0., max(upperLimit, expectedUpperLimit),
                              rtol=1e-03, xtol=1e-06 )
    return trunc_norm_moments(mumax, sigma_exp)
    
    