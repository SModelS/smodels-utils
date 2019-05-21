#!/usr/bin/env python3

""" Try out combinations from pickle file. """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
import pickle, numpy, math
from scipy import optimize
import IPython

f=open("predictions.pcl", "rb" )
predictions = pickle.load ( f )
f.close()

def getExperimentName ( pred ):
    """ returns name of experiment of exp result """
    if "CMS" in pred.expResult.globalInfo.id:
        return "CMS"
    if "ATLAS" in pred.expResult.globalInfo.id:
        return "ATLAS"
    return "???"

def canCombine ( predA, predB, strategy="conservative" ):
    """ can we combine predA and predB? predA and predB can be
        individual predictions, or lists of predictions.
    :param strategy: combination strategy, can be conservative, moderate, aggressive
    """
    if type(predA) == list:
        for pA in predA:
            ret = canCombine ( pA, predB, strategy )
            if ret == False:
                return False
        return True
    if type(predB) == list:
        for pB in predB:
            ret = canCombine ( predA, pB, strategy )
            if ret == False:
                return False
        return True
    if strategy == "conservative":
        return canCombineConservative ( predA, predB )
    if strategy == "moderate":
        return canCombineModerate ( predA, predB )
    if strategy != "aggressive":
        print ( "Error: strategy ``%s'' unknown" % strategy )
        return None
    return canCombineAggressive ( predA, predB )

def canCombineModerate ( predA, predB ):
    """ method that defines what we allow to combine, moderate version.
         """
    if predA.expResult.globalInfo.sqrts != predB.expResult.globalInfo.sqrts:
        return True
    if getExperimentName(predA) != getExperimentName(predB):
        return True
    anaidA = predA.expResult.globalInfo.id
    anaidB = predB.expResult.globalInfo.id
    allowCombination = { "ATLAS-SUSY-2013-02": [ "ATLAS-SUSY-2013-11" ],
                         "CMS-SUS-13-012": [ "CMS-SUS-13-007" ] }
    if anaidA in allowCombination.keys():
        if anaidB in allowCombination[anaidA]:
            return True
    if anaidB in allowCombination.keys():
        if anaidA in allowCombination[anaidB]:
            return True
    return False

def canCombineAggressive ( predA, predB ):
    """ method that defines what we allow to combine, aggressive version.
         """
    if predA.expResult.globalInfo.sqrts != predB.expResult.globalInfo.sqrts:
        return True
    if getExperimentName(predA) != getExperimentName(predB):
        return True
    anaidA = predA.expResult.globalInfo.id
    anaidB = predB.expResult.globalInfo.id
    allowCombination = { "ATLAS-SUSY-2013-02": [ "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-11" ],
                         "CMS-SUS-13-012": [ "CMS-SUS-13-007", "CMS-SUS-13-013" ],
                         "CMS-SUS-12-024": [ "CMS-SUS-13-007", "CMS-SUS-13-013" ],
                         "CMS-SUS-13-007": [ "CMS-SUS-12-024", "CMS-SUS-13-012", "CMS-SUS-13-013" ],
                         "ATLAS-CONF-2013-024": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-037": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054" ],
                         "ATLAS-CONF-2013-047": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-048": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-053": [ "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-054": [ "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ] }
    if anaidA in allowCombination.keys():
        if anaidB in allowCombination[anaidA]:
            return True
    if anaidB in allowCombination.keys():
        if anaidA in allowCombination[anaidB]:
            return True
    return False

def canCombineConservative ( predA, predB ):
    """ method that defines what we allow to combine, conservative version.
         """
    if predA.expResult.globalInfo.sqrts != predB.expResult.globalInfo.sqrts:
        return True
    if getExperimentName(predA) != getExperimentName(predB):
        return True
    return False

def findCompatibles ( predA, predictions, strategy ):
    """ return list of all elements in predictions
        combinable with predA, under the given strategy """
    ret = []
    n=len(predictions)
    for ct,i in enumerate(predictions):
        if canCombine ( predA, i, strategy=strategy ):
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
    print ( "error finding mu hat" )
    return ret

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
            
def findBestCombo ( combinations ):
    """ find the best combo, by computing CLsb values """
    # compute CLsb for all combinations 
    lowestv,lowest=float("inf"),""
    for c in combinations:
        cl_mu = get95CL ( c, expected=True )
        # print ( "95%s expected CL for mu for %s is %.2f" % ( "%", getLetterCode(c), cl_mu) )
        if cl_mu < lowestv:
            lowestv = cl_mu
            lowest = c
    return lowest,lowestv

def getLetterCode ( combination ):
    """ get the letter code of a combination """
    ret = ""
    for c in combination:
        ret += letters[c]
    return ret
def getComboDescription ( combination ):
    return ",".join( [ x.expResult.globalInfo.id for x in combination ] )

## assign a letter to every prediction. for debugging
letters={}
letter=65
for p in predictions:
    letters[p]=chr(letter)
    print ( "Prediction %s: %s" % ( letters[p], p ) )
    letter+=1

for strategy in [ "conservative", "moderate", "aggressive" ]:
    combinables = findCombinations ( predictions, strategy )
    ## optionally, add individual predictions
    combinables += [ [x] for x in predictions ]
    discussCombinations ( combinables )
    bestCombo,ulexp = findBestCombo ( combinables )
    ulobs = get95CL ( bestCombo, expected=False )
    print ( "best combo for strategy ``%s'' is %s: %s: [ul_obs=%.2f, ul_exp=%.2f]" % ( strategy, getLetterCode(bestCombo), getComboDescription(bestCombo), ulobs, ulexp ) ) 

# IPython.embed()
