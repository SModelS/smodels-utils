#!/usr/bin/env python3

""" Try out combinations from pickle file. """

from smodels.theory import decomposer
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.model import Model
import analysisCombiner
import pickle, numpy, math, colorama, copy, sys
from scipy import optimize, stats
# import IPython

class Combiner:
    def __init__ ( self, walkerid=0 ):
        self.walkerid = walkerid

    def getAllPidsOfCombo ( self, combo ):
        """ get all PIDs that make it into one combo """
        pids = set()
        for theoryPred in combo:
            pids = pids.union ( self.getAllPidsOfTheoryPred ( theoryPred ) )
        return pids

    def getAnaIdsWithPids ( self, combo, pids ):
        """ from best combo, retrieve all ana ids that contain *all* pids """
        anaIds = set()
        for theoryPred in combo:
            tpids = self.getAllPidsOfTheoryPred ( theoryPred )
            hasAllPids=True
            for pid in pids:
                if not pid in tpids:
                    hasAllPids=False
                    break
            if hasAllPids:
                anaIds.add ( theoryPred.analysisId() )
        return anaIds

    def getAllPidsOfTheoryPred ( self, pred ):
        """ get all pids that make it into a theory prediction """
        pids = set()
        for prod in pred.PIDs:
            for branch in prod:
                for pid in branch:
                    if type(pid) == list:
                        for p in pid:
                            pids.add ( abs(p) )
                    else:
                        pids.add ( abs(pid) )
        return pids

    def getTheoryPredsWithPids ( self, combo, pids ):
        """ from best combo, retrieve all theory preds that contain *all* pids """
        tpreds = set()
        for theoryPred in combo:
            tpids = self.getAllPidsOfTheoryPred ( theoryPred )
            hasAllPids=True
            for pid in pids:
                if not pid in tpids:
                    hasAllPids=False
                    break
            if hasAllPids:
                tpreds.add ( theoryPred )
        return tpreds

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

    def removeDataType ( self, predictions, dataType ):
        """ remove from the predictions all the ones
        that match dataType """
        if predictions is None:
            return predictions
        tmp = []
        for pred in predictions:
            if pred.dataType() == dataType:
                continue
            tmp.append ( pred )
        self.pprint ( "removed %s, %d/%d remain" % \
                     ( dataType, len(tmp), len(predictions) ) )
        return tmp

    def findCombinations ( self, predictions, strategy ):
        """ finds all allowed combinations of predictions, for
            the given strategy
        :param predictions: list of predictions
        :returns: a list of combinations
        """
        combinables=[]
        n=len(predictions)
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

    def error ( self, *args ):
        self.highlight ( "error", *args )

    def highlight( self, msgType = "info", *args ):
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
        """ simple method that writes some stats about a combination to the log file """
        count={}
        for i in combinables:
            n =len(i)
            if not n in count.keys():
                count[n]=0
            count[n]+=1
        npred = 0
        if 1 in count.keys():
            npred = count[1]
        self.debug ( "%d combinations from %d predictions" % \
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
        letters={}
        if predictions is None:
            return letters
        ## assign a letter to every prediction. for debugging
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

    def getSignificance ( self, combo, expected=False, mumax=None ):
        """ obtain the significance of this combo
        :param expected: get the expected significance, not observed
        :param mumax: maximum muhat before we run into exclusions
        :returns: Z (significance) and muhat ( signal strength multiplier that maximizes Z)
        """
        if len(combo)==0.:
            return 0.,0.
        muhat = self.findMuHat ( combo )
        if mumax is None:
            mumax = float("inf")
        if muhat is None:
            return 0.,0.
        if muhat > mumax:
            self.debug ( "muhat(%.2f) > mumax(%.2f). use mumax" % ( muhat, mumax ) )
            muhat = mumax
        l0 = numpy.array ( [ c.getLikelihood(0.,expected=expected) for c in combo ] )
        LH0 = numpy.prod ( l0[l0!=None] )
        l1 = numpy.array ( [ c.getLikelihood(muhat,expected=expected) for c in combo ] )
        LH1 = numpy.prod ( l1[l1!=None] )
        if LH0 <= 0.:
            self.error ( "likelihood for SM was 0. Set to 1e-80" )
            LH0 = 1e-80
        if LH1 <= 0.:
            self.error ( "likelihood for muhat was 0. Set to 1e-80, muhat was %s" % muhat )
            LH1 = 1e-80
        chi2 = 2 * ( math.log ( LH1 ) - math.log ( LH0 ) ) ## chi2 with one degree of freedom
        if chi2 < 0.:
            chi2 = 0.
        Z = numpy.sqrt ( chi2 )
        return Z, muhat

    def _findLargestZ ( self, combinations, expected=False, mumax=None ):
        """ find the combo with the most significant deviation
        :param expected: find the combo with the most significant expected deviation
        :param mumax: Maximum muhat to allow before we run into an exclusion
        """
        combinations.sort ( key=len, reverse=True ) ## sort them first by length
        # compute CLsb for all combinations
        highestZ,highest,muhat=0.,"",1.
        alreadyDone = [] ## list of combos that have already been looked at.
        ## we will not look at combos that are subsets.
        doProgress=True
        try:
            import progressbar
        except ModuleNotFoundError:
            doProgress=False
        if doProgress:
            import progressbar
            pb = progressbar.ProgressBar(widgets=["combinations",progressbar.Percentage(),
                  progressbar.Bar( marker=progressbar.RotatingMarker() ),
                  progressbar.ETA()])
            pb.maxval = len(combinations)
            pb.start()
        for ctr,c in enumerate(combinations):
            if doProgress:
                pb.update(ctr)
            if self.hasAlreadyDone ( c, alreadyDone ):
                # self.pprint ( "%s is subset of bigger combo. skip." % getLetterCode(c) )
                continue
            Z,muhat_ = self.getSignificance ( c, expected=expected, mumax=mumax )
            if Z == None:
                continue
            # self.pprint ( "[combine] significance for %s is %.2f" % ( self.getLetterCode(c), Z ) )
            if Z > highestZ:
                highestZ = Z
                highest = c
                muhat = muhat_
            alreadyDone.append ( c )
        if doProgress:
            pb.finish()
        return highest,highestZ,muhat

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
            ret = self.getCombinedLikelihood ( combination, mu, nll=True )
            return ret
        for start in [ 0., 1., .1, 10., 1e-2, 1e-3 ]:
            ret = optimize.minimize ( getNLL, start, bounds=[(0.,None)] )
            # print ( "findMuHat combo %s start=%f, ret=%s" % ( combination, start, ret.fun ) )
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

    def priorForNDF ( self, nparticles, nbranchings, nssms, name="expo1",
                      verbose=False, nll=False ):
        """ get the prior for this and this many degrees of freedom
            in the model.
        :param nparticles: number of unfrozen particles
        :param nbranchings: number of branchings > 0 and < 1
        :param nssms: number of signal strength multipliers > 0
        :param name: name of the prior, cause I will be defining quite a few.
        :param verbose: be verbose about computation
        :param nll: if true, compute nll of prior
        :returns: *proper* prior
        """
        if name == "flat":
            prior = 1.
        if name == "expo1":
            a,b,c = 4, 16, 32
            prior = numpy.exp ( -1 * ( nparticles/a + nbranchings/b + nssms/c ) )
        if name == "expo2":
            a,b,c = 3, 3.68*3, 5.7*3
            prior = numpy.exp ( -1 * ( nparticles/a + nbranchings/b + nssms/c ) )
        if name == "gauss1":
            a,b,c = 2, 8, 32 ## the "sigmas" of the Gaussians. Higher values means less punishment
            prior = numpy.exp ( -(1/2) * ( (nparticles/a)**2 + (nbranchings/b)**2 + (nssms/c)**2 ) )
        if verbose:
            self.pprint ( "prior ``%s'': %d particles, %d branchings, %d unique ssms: %.2f" % \
                      ( name, nparticles, nbranchings, nssms, prior ) )
        if nll:
            return - numpy.log ( prior )
        return prior

    def noSuchBranching ( self, branchings, br ):
        """ check if a branching ratio similar to br already exists
            in branchings """
        for cbr in branchings:
            if abs ( cbr - br ) / ( cbr + br ) < 0.025: ## 5 percent rule
                return False
        return True

    def computePrior ( self, protomodel, nll=False, verbose=False, name="expo1" ):
        """ compute the prior for protomodel, used to introduce regularization,
            i.e. punishing for non-zero parameters, imposing sparsity.
        :param nll: if True, return negative log likelihood
        :param verbose: print how you get the prior.
        :param name: name of prior (expo1, gauss1, etc). See self.priorForNDF.
        """
        particles = protomodel.unFrozenParticles ( withLSP=True )
        nparticles = len ( particles )
        nbr = 0
        ## every non-trivial branching costs something
        for mpid,decays in protomodel.decays.items():
            if not mpid in particles or mpid == protomodel.LSP:
                continue ## frozen particles dont count
            memBRs = set() ## memorize branchings, similar branchings count only once
            for dpid,br in decays.items():
                if br > 1e-5 and self.noSuchBranching ( memBRs, br ):
                    memBRs.add ( br )
            tmp = len ( memBRs ) - 1 ## subtract one cause they add up to 1.
            nbr += tmp

        ## every non-trivial signal strength multiplier costs something
        cssms = set()
        for pids,ssm in protomodel.ssmultipliers.items():
            if (abs(pids[0]) not in particles) or (abs(pids[1]) not in particles):
                continue
            ## every unique ssm > 0 and ssm!=1 costs a little, but only very little
            if ssm > 1e-4 and abs ( ssm - 1. ) > .01:
                cssms.add ( int ( 100. * ssm ) )
                # nssms += 1
        # print ( "cssms", cssms )
        ret = self.priorForNDF ( nparticles, nbr, len(cssms), name, verbose )
        if nll:
            return - math.log ( ret )
        return ret

    def computeK ( self, Z, prior ):
        """ compute K from Z and prior (simple) """
        return Z**2 + 2* numpy.log ( prior )

    def selectMostSignificantSR ( self, predictions ):
        """ given, the predictions, for any analysis and topology,
            return the most significant SR only.
        :param predictions: all predictions of all SRs
        :returns: sorted predictions
        """
        print ( "FIXME need to sort predictions for most significant SR first" )
        return predictions

    def findHighestSignificance ( self, predictions, strategy, expected=False,
                                  mumax = None ):
        """ for the given list of predictions and employing the given strategy,
        find the combo with highest significance
        :param expected: find the highest expected significance, not observed
        :param mumax: maximimal signal strength mu that is allowed before we run into an
                      exclusion
        :returns: best combination, significance, likelihood equivalent
        """
        predictions = self.selectMostSignificantSR ( predictions )
        self.letters = self.getLetters ( predictions )
        combinables = self.findCombinations ( predictions, strategy )
        singlepreds = [ [x] for x in predictions ]
        ## optionally, add individual predictions
        combinables = singlepreds + combinables
        self.discussCombinations ( combinables )
        bestCombo,Z,muhat = self._findLargestZ ( combinables, expected=expected, mumax = mumax )
        ## compute a likelihood equivalent for Z
        llhd = stats.norm.pdf(Z)
        # self.pprint ( "bestCombo %s, %s, %s " % ( Z, llhd, muhat ) )
        return bestCombo,Z,llhd,muhat

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

def normalizePrior():
    c = Combiner()
    S=0.
    ctr,nmod=0,30
    control = 0
    for nparticles in range ( 1, 18 ):
        for nbr in range ( 0, 10*nparticles ):
            for nssms in range ( 1, 25*nparticles ):
                t = c.priorForNDF ( nparticles, nbr, nssms, 1. )
                ctr+=1
                control += c.priorForNDF ( nparticles, nbr, nssms, None )
                if ctr % nmod == 0:
                    print ( "nparticles %d, nbr %d, nssms %d, improper prior %.5f" % \
                            ( nparticles, nbr, nssms, t ) )
                    nmod=nmod*2
                S += t
    print ( "The constant for normalizing the prior is %.8f" % (1./S) )
    print ( "With the current normalization we get", control )
    return 1./S

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
    argparser.add_argument ( '-u', '--upper_limits',
            help='use only upper limits results', action='store_true' )
    argparser.add_argument ( '-e', '--efficiencyMaps',
            help='use only efficiency maps results', action='store_true' )
    argparser.add_argument ( '-E', '--expected',
            help='expected values, not observed', action='store_true' )
    argparser.add_argument ( '-P', '--prior',
            help='Compute normalization constant for prior, then quit', action='store_true' )
    args = argparser.parse_args()
    if args.prior:
        normalizePrior()
        sys.exit()
    if args.upper_limits and args.efficiencyMaps:
        print ( "[combiner] -u and -e are mutually exclusive" )
        sys.exit()
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
    anaIds = [ "CMS-SUS-16-033" ]
    anaIds = [ "all" ]
    dts = [ "all" ]
    if args.upper_limits:
        dts = [ "upperLimit" ]
    if args.efficiencyMaps:
        dts = [ "efficiencyMap" ]
    listOfExpRes = db.getExpResults( analysisIDs = anaIds, dataTypes = dts,
                                     onlyWithExpected= True )
    smses = decomposer.decompose ( model, .01*fb )
    #print ( "[combiner] decomposed into %d topos" % len(smses) )
    from smodels.theory.theoryPrediction import theoryPredictionsFor
    combiner = Combiner()
    allps = []
    for expRes in listOfExpRes:
        preds = theoryPredictionsFor ( expRes, smses )
        if preds == None:
            continue
        for pred in preds:
            allps.append ( pred )
    combo,globalZ,llhd,muhat = combiner.findHighestSignificance ( allps, "aggressive", expected=args.expected )
    print ( "[combiner] global Z is %.2f: %s (muhat=%.2f)" % (globalZ, combiner.getComboDescription(combo),muhat ) )
    for expRes in listOfExpRes:
        preds = theoryPredictionsFor ( expRes, smses )
        if preds == None:
            continue
        Z, muhat_ = combiner.getSignificance ( preds, expected=args.expected, mumax = None )
        print ( "%s has %d predictions, local Z is %.2f" % ( expRes.globalInfo.id, len(preds), Z ) )
        for pred in preds:
            pred.computeStatistics()
            tpe = pred.dataType(True)
            tpe += ":" + ",".join ( map ( str, pred.txnames ) )
            print ( "  `- llhd [%s] SM=%.3g BSM=%.3g" % ( tpe, pred.getLikelihood(0.,expected=args.expected), pred.getLikelihood(1.,expected=args.expected) ) )
    comb = Combiner()
