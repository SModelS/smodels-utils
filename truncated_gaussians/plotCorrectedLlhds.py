#!/usr/bin/env python3

from smodels.tools import runtime
import random
runtime._experimental = True
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.tools.statsTools import StatsComputer
from smodels.experiment.databaseObj import Database
from smodels.theory import decomposer
from smodels.tools.truncatedGaussians import TruncatedGaussians
# TruncatedGaussians.newCorrectionType = False
from smodels.theory.model import Model
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from validation.validationHelpers import retrieveValidationFile
import numpy as np
import sys

def setup14021():
    anaid = "CMS-SUS-14-021"
    slhafile = "T2bbWW_111_34_111_34.slha"
    mus = np.arange ( -1.5, 2.01, .03 )
    # alright so this should use the SRSL1c signal region,
    # which has oUL = 5.787E-01*fb and eUL = 5.777E-01*fb
    # however we get oUL_mu = 9.73E-01 and eUL_mu = 8.51E-01
    ret = { "anaid": anaid, "slhafile": slhafile, "mus": mus,
             "combined": False }
    ret["dbpath"]="debug"
    return ret

def setup16033():
    anaid = "CMS-SUS-16-033"
    slhafile = "T2tt_720_80_720_80.slha"
    mus = np.arange ( -1., 1.01, .018 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = False
    ret = { "anaid": anaid, "slhafile": slhafile, "mus": mus,
             "combined": combined }
    ret["dbpath"]="debug"
    return ret

def setup16050():
    anaid = "CMS-SUS-16-050"
    slhafile = "T2tt_720_80_720_80.slha"
    mus = np.arange ( -.4, .6, .006 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = False
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus,
             "combined": combined }

def setup19006():
    anaid = "CMS-SUS-19-006"
    # anaid = "CMS-SUS-19-006-agg"
    slhafile = "T2tt_720_80_720_80.slha"
    mus = np.arange ( -.5, .5, .018 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = True
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus, "combined": combined }

def setup1909():
    anaid = "ATLAS-SUSY-2019-09"
    slhafile = "TChiWZ_300_110_300_110.slha"
    mus = np.arange ( -.5, .5, .018 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = True
    ret = { "anaid": anaid, "slhafile": slhafile, "mus": mus, "combined": combined }
    ret["dbpath"]="debug"
    return ret

def setup20004():
    anaid = "CMS-SUS-20-004"
    slhafile = "TChiHH_200_20_200_20.slha"
    # anaid = "CMS-SUS-19-006-agg"
    mus = np.arange ( -4, 4, .05 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = True
    ret= { "anaid": anaid, "slhafile": slhafile, "mus": mus, "combined": combined }
    return ret

def setup21002():
    anaid = "CMS-SUS-21-002"
    slhafile = "TChiWZ_300_110_300_110.slha"
    mus = np.arange ( -4, 4, .05 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = True
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus, "combined": combined }

class Runner:
    def __init__ ( self, setup ):
        self.setup = setup

    def normalizeLlhds ( self, container : list ):
        T = np.nansum(container)
        if T == 0.:
            return container
        for i,c in enumerate(container):
            container[i]=c/T
        return container

    def normalizeNLLs ( self, container : list ):
        """ for NLLs we just find the minimum """
        if len(container)==0:
            return container
        nllMin = min(container)
        for i,c in enumerate(container):
            container[i]=c-nllMin
        return container

    def wiggle ( self, container : list , r : float = .01 ):
        T = np.nansum(container)
        if T == 0.:
            return
        for i,c in enumerate(container):
            container[i]=c*random.uniform(1-r,1+r)
        return container

    def pprint ( self, *args ):
        if self.setup["verbose"]==False:
            return
        print ( f"[plotCorrectedLlhds] {' '.join(args)}" )

    def runOneSetup ( self ):
        """ run with the given setup """
        doNLL = self.setup["doNLL"]
        db = Database ( self.setup["dbpath"] )
        retrieveValidationFile ( self.setup["slhafile"] )
        combined = self.setup["combined"]
        mus = self.setup["mus"]
        anaid, slhafile, mus = self.setup["anaid"], self.setup["slhafile"], \
                               self.setup["mus"]
        anaidUL = anaid.replace("-agg","").replace("-adl","")

        er = db.getExpResults ( analysisIDs = [ anaidUL ], dataTypes = [ "upperLimit" ] )
        if er == []:
            print ( f"could not find an upperLimit result for {anaid}" )
            return
        erUL = er[0]
        er = db.getExpResults ( analysisIDs = [ anaid ], dataTypes = [ "efficiencyMap" ] )
        if er == []:
            print ( f"could not find an efficiencyMap result for {anaid}" )
            sys.exit()
        erEff = er[0]
        model = Model(BSMparticles=BSMList, SMparticles=SMList)
        model.updateParticles(inputFile=slhafile)
        toplist = decomposer.decompose(model, doCompress=True, doInvisible=True )
        prUL = theoryPredictionsFor(erUL, toplist, combinedResults=False )
        prEff = theoryPredictionsFor(erEff, toplist, combinedResults=combined )
        uls, ul0s, effs, ul20s = [], [], [], []
        ulsE, ul0sE, effsE = [], [], []
        computer0 = StatsComputer.forTruncatedGaussian ( prUL[0], corr = 0. )
        mcorr = 0.3
        computer08 = StatsComputer.forTruncatedGaussian ( prUL[0], corr = mcorr )
        # self.pprint ( f"the limits are observed {computer0.ul}, expected {computer0.eul}" )
        ret = computer0.get_five_values ( False )
        self.pprint ( f"truncated gaussian returned {ret}" )
        for mu in mus:
            ul = prUL[0].likelihood ( mu=mu, return_nll=doNLL )
            #self.pprint ( f"ul for {mu:.2f} is {ul}" )
            if ul == None:
                self.pprint ( f"warning: ul is None for mu={mu:.2f}. (do we have euls?)" )
            uls.append ( ul )
            ul0 = computer0.likelihood ( poi_test=mu, expected=False, return_nll=doNLL )
            ul20 = computer08.likelihood ( poi_test=mu, expected=False, return_nll=doNLL )
            ul0s.append ( ul0 )
            ul20s.append ( ul20 )
            effN = prEff[0].likelihood ( mu=mu, return_nll=True )
            # self.pprint ( f"llhd for {prEff[0].dataId()} {mu:.2f} is {effN},{eff}" )
            effs.append ( effN )
            if self.setup["addExpectations"]:
                ulE = prUL[0].likelihood ( mu=mu, expected=True, return_nll=doNLL )
                ulsE.append ( ulE )
                ul0E = computer0.likelihood ( poi_test=mu, expected=True, return_nll=doNLL )
                ul0sE.append ( ul0E )
                effE = prEff[0].likelihood ( mu=mu, expected=True, return_nll=True )
                effsE.append ( effE )
        if not doNLL:
            if len(effs)>0:
                T = min(effs)
                for i,x in enumerate(effs):
                    effs[i]=np.exp( T-x )
            if len(effsE)>0:
                T = min(effsE)
                for i,x in enumerate(effsE):
                    effsE[i]=np.exp( T-x )

        for x in [ uls, ul0s, effs, ulsE, ul0sE, effsE, ul20s ]:
            if doNLL:
                self.normalizeNLLs ( x )
            else:
                self.normalizeLlhds ( x )
        self.wiggle ( uls )
        from smodels_utils.plotting import mpkitty as plt
        plt.plot ( mus, uls, label = "from limits, corr=0.6", c="r" )
        plt.plot ( mus, ul0s, label = "from limits, no corr", c="g" )
        plt.plot ( mus, ul20s, label = f"from limits, corr={mcorr:.1f}", c="b" )
        plt.plot ( mus, effs, label = "from efficiencies", c="k", lw=2 )
        if self.setup["addExpectations"]:
            plt.plot ( mus, ulsE, label = "from limits, corr=0.6, expected", c="r", ls="dotted" )
            plt.plot ( mus, ul0sE, label = "from limits, no corr, expected", c="g", ls="dotted" )
            plt.plot ( mus, effsE, label = "from efficiencies, expected", ls="dotted", c="k" )
        plt.xlabel ( r"$\mu$" )
        plt.title ( f"comparison of likelihoods, {anaid}" )
        plt.legend()
        plt.savefig ( f"{anaid}.png" )
        plt.show()

def defaults ( ):
    """ define some default values """
    ret= {}
    ret["dbpath"]="debug"
    ret["dbpath"]="official"
    ret["dbpath"]="../../smodels-database"
    ret["doNLL"]=True
    ret["addExpectations"]=False
    ret["verbose"]=False
    return ret

def override ( setup, args ):
    if args.llhds:
        setup["doNLL"]=False
    if args.expectations:
        setup["addExpectations"]=True
    if args.verbose:
        setup["verbose"]=True
    return setup

def allSetups():
    ret = []
    for g in globals():
        if "setup" in g and not "all" in g:
            ret.append ( g )
    return ret

def run():
    import argparse
    argparser = argparse.ArgumentParser(description=
                  'a tool to compare likelihood plots')
    argparser.add_argument ( '-a', '--analysis', nargs='?',
                        help='analysis', type=str, default=None )
    argparser.add_argument ( '-l', '--llhds', help="likelihoods, not NLLs",
                        action="store_true" )
    argparser.add_argument ( '-e', '--expectations', help="add expectations",
                        action="store_true" )
    argparser.add_argument ( '-v', '--verbose', help="be verbose",
                        action="store_true" )
    args=argparser.parse_args()
    if args.analysis is None:
        print ( "specify an analysis" )
        sys.exit()
    if args.analysis == "all":
        for g in allSetups():
            setup = defaults( )
            func = globals()[g]
            add = func()
            setup.update ( add )
            override ( setup, args )
            print ( f"running {setup['anaid']}" )
            runner = Runner ( setup )
            runner.runOneSetup ( )
        return

    method = f"setup{args.analysis}"
    if not method in globals():
        print ( f"method {method} not found. we have " )
        for g in globals():
            if "setup" in g and not "all" in g:
                print ( "--", g )
    func = globals()[method]
    setup = defaults()
    add = func()
    setup.update (add )
    if args.llhds:
        setup["doNLL"]=False
    if args.expectations:
        setup["addExpectations"]=True
    if args.verbose:
        setup["verbose"]=True
    override ( setup, args )
    runner = Runner ( setup )
    runner.runOneSetup ( )

if __name__ == "__main__":
    run()
