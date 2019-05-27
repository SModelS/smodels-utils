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

class Combiner:
    def __init__ ( self ):
        pass

    def findCompatibles ( self, predA, predictions, strategy ):
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
                    deeper = self.findCompatibles ( combo, predictions[ct+1:], strategy )
                    for d in deeper:
                        ret.append ( d )
        return ret

    def findCombinations ( self, predictions, strategy ):
        """ finds all allowed combinations of predictions, for
            the given strategy
        :param predictions: list of predictions
        :returns: a list of combinations
        """
        combinables=[]
        n=len(predictions)
        # print ( "[Combiner] %d predictions" % n )
        for iA,predA in enumerate(predictions):
            combo = [ predA ]
            nexti = iA + 1 
            compatibles = self.findCompatibles ( predA, predictions[nexti:], strategy )
            combinables += compatibles
        return combinables

    def discussCombinations ( self, combinables ):
        count={}
        for i in combinables:
            # print ( "combo %s" % ", ".join ( [ x.expResult.globalInfo.id for x in i ] ))
            n =len(i)
            if not n in count.keys():
                count[n]=0
            count[n]+=1
        npred = 0
        if 1 in count.keys():
            npred = count[1]
        print ( "[combiner] %d combinations from %d predictions" % \
                (len(combinables),npred) )
        #for k,v in count.items():
        #    print ( "[combine] %d combinations with %d predictions" % ( v, k ) )

    def getCombinedLikelihood ( self, combination, mu, expected=False, nll=False ):
        """ get the combined likelihood for a signal strength mu 
        :param nll: compute the negative log likelihood
        """
        ret = numpy.prod ( [ c.getLikelihood(mu,expected=expected) for c in combination ] )
        if nll:
            if ret <= 0.:
                ret = 1e-70
            ret = - math.log ( ret )
        return ret

    def printLLhds ( self, llhds ):
        keys = list ( llhds.keys() )
        keys.sort()
        for k in keys:
            v=llhds[k]
            print ( "[combiner] %.2f: %.3g" % ( k, v ) )


    def isSubset ( self, small, big ):
        """ is the small combo a subset of the big combo? """
        for s in small:
            if not s in big:
                return False
        return True

    def hasAlreadyDone ( self, small, combos ):
        """ is the small combo already a subset of any of the
            combos in 'combos'? """
        for c in combos:
            if self.isSubset ( small, c ):
                return True
        return False

    def findBestCombo ( self, combinations ):
        """ find the best combo, by computing CLsb values """
        combinations.sort ( key=len, reverse=True ) ## sort them first be length
        # compute CLsb for all combinations 
        lowestv,lowest=float("inf"),""
        alreadyDone = [] ## list of combos that have already been looked at.
        ## we will not look at combos that are subsets.
        for c in combinations:
            if self.hasAlreadyDone ( c, alreadyDone ):
                # print ( "%s is subset of bigger combo. skip." % getLetterCode(c) )
                continue
            cl_mu = self.get95CL ( c, expected=True )
            if cl_mu == None:
                continue
            # print ( "95%s expected CL for mu for %s is %.2f" % ( "%", getLetterCode(c), cl_mu) )
            if cl_mu < lowestv:
                lowestv = cl_mu
                lowest = c
            alreadyDone.append ( c )
        return lowest,lowestv

    def getLetters( self, predictions ):
        ## assign a letter to every prediction. for debugging
        letters={}
        letter=65
        # print ( "[combine] Letters assigned to results:" )
        for p in predictions:
            letters[p]=chr(letter)
            # print ( "[combine] Prediction %s: %s" % ( letters[p], p.expResult.globalInfo.id ) )
            letter+=1
        return letters


    def getComboDescription ( self, combination ):
        return ",".join( [ x.expResult.globalInfo.id for x in combination ] )

    def getSignificance ( self, combo ):
        """ obtain the significance of this combo """
        muhat = self.findMuHat ( combo )
        if muhat == None:
            return 0.
        LH0 = numpy.prod ( [ c.getLikelihood(0.,expected=False) for c in combo ] )
        LH1 = numpy.prod ( [ c.getLikelihood(muhat,expected=False) for c in combo ] )
        if LH0 <= 0.:
            LH0 = 1e-80
        if LH1 <= 0.:
            LH1 = 1e-80
        chi2 = 2 * ( math.log ( LH1 ) - math.log ( LH0 ) ) ## chi2 with one degree of freedom
        # p = 1 - stats.chi2.cdf ( chi2, 1. )
        # Z = stats.norm.ppf ( p )
        if chi2 < 0.:
            chi2 = 0.
        Z = numpy.sqrt ( chi2 )
        # print ( "chi2,Z=", chi2, Z )
        ## FIXME compute significance from chi2
        return Z

    def _findLargestZ ( self, combinations ):
        """ find the combo with the most significant deviation """
        combinations.sort ( key=len, reverse=True ) ## sort them first be length
        # compute CLsb for all combinations 
        highestZ,highest=0.,""
        alreadyDone = [] ## list of combos that have already been looked at.
        ## we will not look at combos that are subsets.
        for c in combinations:
            if self.hasAlreadyDone ( c, alreadyDone ):
                # print ( "%s is subset of bigger combo. skip." % getLetterCode(c) )
                continue
            Z = self.getSignificance ( c )
            if Z == None:
                continue
            # print ( "[combine] significance for %s is %.2f" % ( self.getLetterCode(c), Z ) )
            if Z > highestZ:
                highestZ = Z
                highest = c
            alreadyDone.append ( c )
        return highest,highestZ

    def get95CL ( self, combination, expected ):
        """ compute the CLsb value for one specific combination 
        :param expected: compute expected instead of observed value
        """
        llhds={}
        muhat = self.findMuHat ( combination )
        if muhat == None:
            return None
        Lmuhat = self.getCombinedLikelihood ( combination, muhat, expected=expected )
        # mumin=muhat/3.
        # Lmumin = getCombinedLikelihood ( combination, mumin, expected=expected )
        mumin = 0.
        mumax = muhat
        while True:
            mumax=2.*mumax+0.5
            Lmumax = self.getCombinedLikelihood ( combination, mumax, expected=expected )
            if Lmumax / Lmuhat < 1e-3: ## less than 1 permille? stop!
                break
        dmu = ( mumax - mumin ) / 30.
        for mu in numpy.arange(mumin,mumax,dmu): ## scan mu
            L = self.getCombinedLikelihood ( combination, mu, expected=expected )
            llhds[mu]=L
        # self.printLLhds ( llhds )
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

    def findMuHat ( self, combination ):
        """ find the maximum likelihood estimate for the signal strength mu """
        def getNLL ( mu ):
            return self.getCombinedLikelihood ( combination, mu, nll=True )
        ret = optimize.minimize ( getNLL, 1., bounds=[(0.,None)] )
        if ret.status==0:
            return ret.x[0]
        print ( "[combine] error finding mu hat for %s" % self.getLetterCode(combination) )
        return None

    def getLetterCode ( self, combination ):
        """ get the letter code of a combination """
        ret = ""
        for c in combination:
            ret += self.letters[c]
        return ret

    def findHighestSignificance ( self, predictions, strategy ):
        """ for the given list of predictions and employing the given strategy,
        find the combo with highest significance 
        :returns: best combination, significance, likelihood equivalent
        """
        self.letters = self.getLetters ( predictions )
        combinables = self.findCombinations ( predictions, strategy )
        singlepreds = [ [x] for x in predictions ]
        ## optionally, add individual predictions
        combinables = singlepreds + combinables
        self.discussCombinations ( combinables )
        bestCombo,Z = self._findLargestZ ( combinables )
        ## compute a likelihood equivalent for Z
        llhd = stats.norm.pdf(Z)
        return bestCombo,Z,llhd

    def findStrongestExclusion ( self, predictions, strategy ):
        """ for the given list of predictions and employing the given strategy,
        find the combo with strongest exclusion """
        self.letters = getLetters ( predictions )
        print ()
        print ( "[combine] Find the strongest exclusion using strategy: %s" % strategy )
        combinables = self.findCombinations ( predictions, strategy )
        singlepreds = [ [x] for x in predictions ]
        ## optionally, add individual predictions
        combinables = singlepreds + combinables
        discussCombinations ( combinables )
        bestCombo,ulexp = findBestCombo ( combinables )
        ulobs = get95CL ( bestCombo, expected=False )
        print ( "[combine] best combo for strategy ``%s'' is %s: %s: [ul_obs=%.2f, ul_exp=%.2f]" % ( strategy, self.getLetterCode(bestCombo), self.getComboDescription(bestCombo), ulobs, ulexp ) ) 
        return bestCombo,ulexp,ulobs

if __name__ == "__main__":
    f=open("predictions.pcl", "rb" )
    predictions = pickle.load ( f )
    f.close()
    algo = Combiner ()
    print ()
    strategy = "aggressive"
    print ( "Find highest significance for: %s" % strategy )
    bestCombo,Z,llhd = algo.findHighestSignificance ( predictions, strategy )
    print ( "best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( strategy, algo.getLetterCode(bestCombo), algo.getComboDescription(bestCombo), Z ) ) 
