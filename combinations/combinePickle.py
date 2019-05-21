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
    return canCombineAggressive ( predA, predB )

def canCombineAggressive ( predA, predB ):
    """ method that defines what we allow to combine, conservative version.
         """
    if predA.expResult.globalInfo.sqrts != predB.expResult.globalInfo.sqrts:
        return True
    if getExperimentName(predA) != getExperimentName(predB):
        return True
    anaidA = predA.expResult.globalInfo.id
    anaidB = predB.expResult.globalInfo.id
    return False

def canCombineConservative ( predA, predB ):
    """ method that defines what we allow to combine, conservative version.
         """
    if predA.expResult.globalInfo.sqrts != predB.expResult.globalInfo.sqrts:
        return True
    if getExperimentName(predA) != getExperimentName(predB):
        return True
    return False

def findCompatibles ( predA, predictions ):
    """ return list of all elements in predictions
        combinable with predA """
    ret = []
    n=len(predictions)
    for ct,i in enumerate(predictions):
        if canCombine ( predA, i ):
            lpredA, li = predA, i
            if type(predA)!=list:
                lpredA = [ predA ]
            if type(i)!=list:
                li = [ i ]
            combo = lpredA + li
            ret.append ( combo )
            if ct < n:
                deeper = findCompatibles ( combo, predictions[ct+1:] )
                for d in deeper:
                    ret.append ( d )
    return ret

def findCombinations ( predictions ):
    """ finds all allowed combinations of predictions 
    :param predictions: list of predictions
    :returns: a list of combinations
    """
    combinables=[]
    n=len(predictions)
    print ( "%d predictions" % n )
    for iA,predA in enumerate(predictions):
        combo = [ predA ]
        nexti = iA + 1 
        compatibles = findCompatibles ( predA, predictions[nexti:] )
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
    ret = optimize.minimize ( getNLL, 1. )
    return ret

def get95CL ( combination ):
    """ compute the CLsb value for one specific combination """
    llhds={}
    muhat = findMuHat ( combination )
    print ( "muhat=", muhat )
    for mu in numpy.arange(.5,2.,.05): ## scan mu
        L = getCombinedLikelihood ( combination, mu, expected=True )
        llhds[mu]=L
    Sm = sum ( llhds.values() )
    C = 0.
    for k,v in llhds.items():
        C+=v/Sm
        if C>.95:
            return k
    return 1.
            
def findBestCombo ( combinations ):
    """ find the best combo, by computing CLsb values """
    # compute CLsb for all combinations 
    lowestv,lowest=float("inf"),""
    for c in combinations:
        cl_mu = get95CL ( c, expected=True )
        print ( "95%s expected CL for mu for %s is %.2f" % ( "%", getLetterCode(c), cl_mu) )
        if cl_mu < lowestv:
            lowestv = cl_mu
            lowest = c
    return lowest,lowestv

## assign a letter to every prediction. for debugging
letters={}
letter=65
for p in predictions:
    letters[p]=chr(letter)
    letter+=1

def getLetterCode ( combination ):
    """ get the letter code of a combination """
    ret = ""
    for c in combination:
        ret += letters[c]
    return ret
def getComboDescription ( combination ):
    return ",".join( [ x.expResult.globalInfo.id for x in combination ] )

combinables = findCombinations ( predictions )
## optionally, add individual predictions
combinables += [ [x] for x in predictions ]
discussCombinations ( combinables )
bestCombo,ulexp = findBestCombo ( combinables )
ulobs = get95CL ( bestCombo, expected=False )
print ( "best combo is %s: %s: [ul_obs=%.2f, ul_exp=%.2f]" % ( getLetterCode(bestCombo), getComboDescription(bestCombo), ulobs, ulexp ) ) 

# IPython.embed()
