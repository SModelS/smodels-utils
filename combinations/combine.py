#!/usr/bin/env python3

""" Try out combinations from pickle file. """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
import analysisCombiner
import pickle, numpy, math
from scipy import optimize, stats
import IPython

f=open("predictions.pcl", "rb" )
predictions = pickle.load ( f )
f.close()

def findCompatibles ( predA, predictions, strategy ):
    """ return list of all elements in predictions
        combinable with predA, under the given strategy """
    ret = []
    n=len(predictions)
    for ct,i in enumerate(predictions):
        if analysisCombiner.canCombine ( predA, i, strategy=strategy ):
            lpredA, li = predA, i
            if type(predA)!=list:
                lpredA = [ predA ]
            if type(i)!=list:
                li = [ i ]
            combo = lpredA + li
            ret.append ( combo )
            if ct < n:
                deeper = findCompatibles ( combo, predictions[ct+1:], strategy )
                for d in deeper:
                    ret.append ( d )
    return ret

def findCombinations ( predictions, strategy ):
    """ finds all allowed combinations of predictions, for
        the given strategy
    :param predictions: list of predictions
    :returns: a list of combinations
    """
    combinables=[]
    n=len(predictions)
    print ( "%d predictions" % n )
    for iA,predA in enumerate(predictions):
        combo = [ predA ]
        nexti = iA + 1 
        compatibles = findCompatibles ( predA, predictions[nexti:], strategy )
        combinables += compatibles
    return combinables

def discussCombinations ( combinables ):
    count={}
    for i in combinables:
        # print ( "combo %s" % ", ".join ( [ x.expResult.globalInfo.id for x in i ] ))
        n =len(i)
        if not n in count.keys():
            count[n]=0
        count[n]+=1
    print ( "%d combinations" % len(combinables) )
    for k,v in count.items():
        print ( "%d combinations with %d predictions" % ( v, k ) )

def getCombinedLikelihood ( combination, mu, expected=False, nll=False ):
    """ get the combined likelihood for a signal strength mu 
    :param nll: compute the negative log likelihood
    """
    ret = numpy.prod ( [ c.getLikelihood(mu,expected=expected) for c in combination ] )
    if nll:
        ret = - math.log ( ret )
    return ret

def findMuHat ( combination ):
    """ find the maximum likelihood estimate for the signal strength mu """
    def getNLL ( mu ):
        return getCombinedLikelihood ( combination, mu, nll=True )
    ret = optimize.minimize ( getNLL, 1., bounds=[(0.,None)] )
    if ret.status==0:
        return ret.x[0]
    print ( "error finding mu hat for %s" % getLetterCode(combination) )
    return None

def printLLhds ( llhds ):
    keys = list ( llhds.keys() )
    keys.sort()
    for k in keys:
        v=llhds[k]
        print ( "%.2f: %.3g" % ( k, v ) )

def get95CL ( combination, expected ):
    """ compute the CLsb value for one specific combination 
    :param expected: compute expected instead of observed value
    """
    llhds={}
    muhat = findMuHat ( combination )
    if muhat == None:
        return None
    Lmuhat = getCombinedLikelihood ( combination, muhat, expected=expected )
    # mumin=muhat/3.
    # Lmumin = getCombinedLikelihood ( combination, mumin, expected=expected )
    mumin = 0.
    mumax = muhat
    while True:
        mumax=2.*mumax+0.5
        Lmumax = getCombinedLikelihood ( combination, mumax, expected=expected )
        if Lmumax / Lmuhat < 1e-3: ## less than 1 permille? stop!
            break
    dmu = ( mumax - mumin ) / 30.
    for mu in numpy.arange(mumin,mumax,dmu): ## scan mu
        L = getCombinedLikelihood ( combination, mu, expected=expected )
        llhds[mu]=L
    # printLLhds ( llhds )
    Sm = sum ( llhds.values() )
    C = 0.
    for x,v in llhds.items():
        Cold = C
        C+=v/Sm
        if C>.95:
            k = v/Sm / ( x - xold )
            d = C - k*x
            return ( 0.95 - d ) / k
            # return xold + ( x - xold ) * ( C - Cold )
        xold = x
    return 1.

def isSubset ( small, big ):
    """ is the small combo a subset of the big combo? """
    for s in small:
        if not s in big:
            return False
    return True

def hasAlreadyDone ( small, combos ):
    """ is the small combo already a subset of any of the
        combos in 'combos'? """
    for c in combos:
        if isSubset ( small, c ):
            return True
    return False

def findBestCombo ( combinations ):
    """ find the best combo, by computing CLsb values """
    combinations.sort ( key=len, reverse=True ) ## sort them first be length
    # compute CLsb for all combinations 
    lowestv,lowest=float("inf"),""
    alreadyDone = [] ## list of combos that have already been looked at.
    ## we will not look at combos that are subsets.
    for c in combinations:
        if hasAlreadyDone ( c, alreadyDone ):
            # print ( "%s is subset of bigger combo. skip." % getLetterCode(c) )
            continue
        cl_mu = get95CL ( c, expected=True )
        if cl_mu == None:
            continue
        # print ( "95%s expected CL for mu for %s is %.2f" % ( "%", getLetterCode(c), cl_mu) )
        if cl_mu < lowestv:
            lowestv = cl_mu
            lowest = c
        alreadyDone.append ( c )
    return lowest,lowestv

def getSignificance ( combo ):
    """ obtain the significance of this combo """
    muhat = findMuHat ( combo )
    if muhat == None:
        return 0.
    LH0 = numpy.prod ( [ c.getLikelihood(0.,expected=False) for c in combo ] )
    LH1 = numpy.prod ( [ c.getLikelihood(muhat,expected=False) for c in combo ] )
    chi2 = 2 * ( math.log ( LH1 ) - math.log ( LH0 ) ) ## chi2 with one degree of freedom
    # p = 1 - stats.chi2.cdf ( chi2, 1. )
    # Z = stats.norm.ppf ( p )
    Z = numpy.sqrt ( chi2 )
    # print ( "chi2,Z=", chi2, Z )
    ## FIXME compute significance from chi2
    return Z

def findLargestSignificance ( combinations ):
    """ find the combo with the most significant deviation """
    combinations.sort ( key=len, reverse=True ) ## sort them first be length
    # compute CLsb for all combinations 
    highestZ,highest=0.,""
    alreadyDone = [] ## list of combos that have already been looked at.
    ## we will not look at combos that are subsets.
    for c in combinations:
        if hasAlreadyDone ( c, alreadyDone ):
            # print ( "%s is subset of bigger combo. skip." % getLetterCode(c) )
            continue
        Z = getSignificance ( c )
        if Z == None:
            continue
        print ( "significance for %s is %.2f" % ( getLetterCode(c), Z ) )
        if Z > highestZ:
            highestZ = Z
            highest = c
        alreadyDone.append ( c )
    return highest,highestZ


def getLetterCode ( combination ):
    """ get the letter code of a combination """
    ret = ""
    for c in combination:
        ret += letters[c]
    return ret
def getComboDescription ( combination ):
    return ",".join( [ x.expResult.globalInfo.id for x in combination ] )

def getLetters( predictions ):
    ## assign a letter to every prediction. for debugging
    letters={}
    letter=65
    print ( "Letters assigned to results:" )
    for p in predictions:
        letters[p]=chr(letter)
        print ( "Prediction %s: %s" % ( letters[p], p.expResult.globalInfo.id ) )
        letter+=1
    return letters

letters = getLetters ( predictions )

# for strategy in [ "conservative", "moderate", "aggressive" ]:
for strategy in [ "aggressive" ]:
    print ()
    print ( "Combine: %s" % strategy )
    combinables = findCombinations ( predictions, strategy )
    singlepreds = [ [x] for x in predictions ]
    ## optionally, add individual predictions
    combinables = singlepreds + combinables
    discussCombinations ( combinables )
    bestCombo,Z = findLargestSignificance ( combinables )
    print ( "best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( strategy, getLetterCode(bestCombo), getComboDescription(bestCombo), Z ) ) 

    #bestCombo,ulexp = findBestCombo ( combinables )
    #ulobs = get95CL ( bestCombo, expected=False )
    #print ( "best combo for strategy ``%s'' is %s: %s: [ul_obs=%.2f, ul_exp=%.2f]" % ( strategy, getLetterCode(bestCombo), getComboDescription(bestCombo), ulobs, ulexp ) ) 

# IPython.embed()
