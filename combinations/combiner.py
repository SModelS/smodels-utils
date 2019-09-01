#!/usr/bin/env python3

""" Try out combinations from pickle file. """

from smodels.theory import decomposer
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.model import Model
import analysisCombiner
import pickle, numpy, math, colorama, copy
from scipy import optimize, stats
# import IPython

class Combiner:
    def __init__ ( self, walkerid=0 ):
        self.walkerid = walkerid

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

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[walk:%d] %s%s" % ( col, self.walkerid, " ".join(map(str,args)), colorama.Fore.RESET ) )

    def error ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[walk:%d] %s%s" % ( col, self.walkerid, " ".join(map(str,args)), colorama.Fore.RESET ) )

    def pprint ( self, *args ):
        """ logging """
        print ( "[combine:%d] %s" % (self.walkerid, " ".join(map(str,args))) )

    def debug ( self, *args ):
        """ logging """
        pass # default is, do nothing

    def discussCombinations ( self, combinables ):
        count={}
        for i in combinables:
            n =len(i)
            if not n in count.keys():
                count[n]=0
            count[n]+=1
        npred = 0
        if 1 in count.keys():
            npred = count[1]
        self.pprint ( "%d combinations from %d predictions" % \
                      (len(combinables),npred) )

    def getCombinedLikelihood ( self, combination, mu, expected=False, nll=False ):
        """ get the combined likelihood for a signal strength mu
        :param nll: compute the negative log likelihood
        """
        llhds = numpy.array ( [ c.getLikelihood(mu,expected=expected) for c in combination ] )
        ret = numpy.prod ( llhds[llhds!=None] )
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
            self.pprint ( "%.2f: %.3g" % ( k, v ) )


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
                # self.pprint ( "%s is subset of bigger combo. skip." % getLetterCode(c) )
                continue
            cl_mu = self.get95CL ( c, expected=True )
            if cl_mu == None:
                continue
            # self.pprint ( "95%s expected CL for mu for %s is %.2f" % ( "%", getLetterCode(c), cl_mu) )
            if cl_mu < lowestv:
                lowestv = cl_mu
                lowest = c
            alreadyDone.append ( c )
        return lowest,lowestv

    def getLetters( self, predictions ):
        ## assign a letter to every prediction. for debugging
        letters={}
        letter=65
        # self.pprint ( "[combine] Letters assigned to results:" )
        for p in predictions:
            letters[p]=chr(letter)
            # self.pprint ( "[combine] Prediction %s: %s" % ( letters[p], p.expResult.globalInfo.id ) )
            letter+=1
        return letters


    def getComboDescription ( self, combination ):
        def describe ( x ):
            return "%s(%s)" % ( x.analysisId(), x.dataType().replace("upperLimit", "ul" ).replace ( "efficiencyMap", "em" ).replace ( "combined", "comb" ) )
        return ",".join( [ describe(x) for x in combination ] )

    def getSignificance ( self, combo, expected=False ):
        """ obtain the significance of this combo
        :param expected: get the expected significance, not observed
        """
        muhat = self.findMuHat ( combo )
        if muhat == None:
            return 0.
        l0 = numpy.array ( [ c.getLikelihood(0.,expected=expected) for c in combo ] )
        LH0 = numpy.prod ( l0[l0!=None] )
        l1 = numpy.array ( [ c.getLikelihood(muhat,expected=expected) for c in combo ] )
        LH1 = numpy.prod ( l1[l1!=None] )
        if LH0 <= 0.:
            logger.error ( "likelihood for SM was 0. Set to 1e-80" )
            LH0 = 1e-80
        if LH1 <= 0.:
            logger.error ( "likelihood for muhat was 0. Set to 1e-80, muhat was %s" % muhat )
            LH1 = 1e-80
        chi2 = 2 * ( math.log ( LH1 ) - math.log ( LH0 ) ) ## chi2 with one degree of freedom
        # p = 1 - stats.chi2.cdf ( chi2, 1. )
        # Z = stats.norm.ppf ( p )
        if chi2 < 0.:
            chi2 = 0.
        Z = numpy.sqrt ( chi2 )
        # self.pprint ( "chi2,Z=", chi2, Z )
        ## FIXME compute significance from chi2
        if Z > 29.:
           self.pprint ( "I just computed the significance. It is %.2f. What the fuck. lh1=%g, lh0=%g" % (Z, LH1, LH0 ) )
        return Z

    def _findLargestZ ( self, combinations, expected=False ):
        """ find the combo with the most significant deviation
        :param expected: find the combo with the most significant expected deviation
        """
        combinations.sort ( key=len, reverse=True ) ## sort them first be length
        # compute CLsb for all combinations
        highestZ,highest=0.,""
        alreadyDone = [] ## list of combos that have already been looked at.
        ## we will not look at combos that are subsets.
        for c in combinations:
            if self.hasAlreadyDone ( c, alreadyDone ):
                # self.pprint ( "%s is subset of bigger combo. skip." % getLetterCode(c) )
                continue
            Z = self.getSignificance ( c, expected=expected )
            if Z == None:
                continue
            # self.pprint ( "[combine] significance for %s is %.2f" % ( self.getLetterCode(c), Z ) )
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
        start = 1.
        for start in [ 1., .1, 10., 1e-3 ]:
            ret = optimize.minimize ( getNLL, start, bounds=[(0.,None)] )
            if ret.status==0:
                return ret.x[0]
        self.pprint ( "%serror finding mu hat for %s%s" % (colorama.Fore.RED, self.getLetterCode(combination), colorama.Fore.RESET ) )
        return None

    def getLetterCode ( self, combination ):
        """ get the letter code of a combination """
        ret = ""
        for c in combination:
            ret += self.letters[c]
        return ret

    def findHighestSignificance ( self, predictions, strategy, expected=False ):
        """ for the given list of predictions and employing the given strategy,
        find the combo with highest significance
        :param expected: find the highest expected significance, not observed
        :returns: best combination, significance, likelihood equivalent
        """
        self.letters = self.getLetters ( predictions )
        combinables = self.findCombinations ( predictions, strategy )
        singlepreds = [ [x] for x in predictions ]
        ## optionally, add individual predictions
        combinables = singlepreds + combinables
        self.discussCombinations ( combinables )
        bestCombo,Z = self._findLargestZ ( combinables, expected=expected )
        ## compute a likelihood equivalent for Z
        llhd = stats.norm.pdf(Z)
        return bestCombo,Z,llhd

    def removeDataFromBestCombo ( self, bestCombo ):
        """ remove the data from all theory predictions, we dont need them. """
        self.debug ( "removing Data from best Combo " )
        for ci,combo in enumerate(bestCombo):
            if hasattr ( combo, "elements" ):
                del bestCombo[ci].elements
            if hasattr ( combo, "avgElement" ):
                del bestCombo[ci].avgElement
            eR = bestCombo[ci].expResult
            for ds in eR.datasets:
                for tx in ds.txnameList:
                    if hasattr ( tx, "txnameData" ):
                        del tx.txnameData
                    if hasattr ( tx, "txnameDataExp" ):
                        del tx.txnameDataExp
        return bestCombo

    def removeDataFromTheoryPred ( self, tp ):
        """ remove unnecessary stuff from a theoryprediction object.
            for storage. """
        self.debug ( "removing data from theory pred %s" % tp.analysisId() )
        theorypred = copy.deepcopy( tp )
        if hasattr ( theorypred, "elements" ):
            del theorypred.elements
        if hasattr ( theorypred, "avgElement" ):
            del theorypred.avgElement
        eR = theorypred.expResult
        for ds in eR.datasets:
            for tx in ds.txnameList:
                if hasattr ( tx, "txnameData" ):
                    del tx.txnameData
                if hasattr ( tx, "txnameDataExp" ):
                    del tx.txnameDataExp
        return theorypred

    """
    def findStrongestExclusion ( self, predictions, strategy ):
        # for the given list of predictions and employing the given strategy,
        # find the combo with strongest exclusion
        self.letters = getLetters ( predictions )
        self.pprint ( "Find the strongest exclusion using strategy: %s" % strategy )
        combinables = self.findCombinations ( predictions, strategy )
        singlepreds = [ [x] for x in predictions ]
        ## optionally, add individual predictions
        combinables = singlepreds + combinables
        discussCombinations ( combinables )
        bestCombo,ulexp = findBestCombo ( combinables )
        ulobs = get95CL ( bestCombo, expected=False )
        self.pprint ( "best combo for strategy ``%s'' is %s: %s: [ul_obs=%.2f, ul_exp=%.2f]" % ( strategy, self.getLetterCode(bestCombo), self.getComboDescription(bestCombo), ulobs, ulexp ) )
        return bestCombo,ulexp,ulobs
    """

if __name__ == "__main__":
    from smodels.tools import runtime
    runtime._experimental = True
    import argparse
    argparser = argparse.ArgumentParser(
            description='combiner. if called from commandline, computes the highest Z' )
    argparser.add_argument ( '-f', '--slhafile',
            help='slha file to test [test.slha]',
            type=str, default="test.slha" )
    argparser.add_argument ( '-d', '--database',
            help='path to database [../../smodels-database]',
            type=str, default="../../smodels-database" )
    args = argparser.parse_args()
    from smodels.experiment.databaseObj import Database
    from smodels.theory import decomposer
    from smodels.particlesLoader import BSMList
    from smodels.share.models.SMparticles import SMList
    from smodels.theory.model import Model
    from smodels.tools.physicsUnits import fb
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=args.slhafile)
    print ( "[combiner] loading database", args.database )
    db = Database ( args.database )
    print ( "[combiner] done loading database" )
    listOfExpRes = db.getExpResults()
    smses = decomposer.decompose ( model, .01*fb )
    print ( "[combiner] decomposed into %d topos" % len(smses) )
    from smodels.theory.theoryPrediction import theoryPredictionsFor
    for expRes in listOfExpRes:
        preds = theoryPredictionsFor ( expRes, smses )
        if preds == None:
            continue
        print ( "%s has %d predictions" % ( expRes.globalInfo.id, len(preds) ) )
        for pred in preds:
            pred.computeStatistics()
            print ( "likelihood %s %s %s" % ( pred.dataType(True), pred.getLikelihood(0.), pred.getLikelihood(1.) ) )
    comb = Combiner()


