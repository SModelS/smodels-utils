#!/usr/bin/env python3

import sys
sys.path.insert(0,"../smodels-utils/")
sys.path.insert(0,"../smodels-utils/validation/")
sys.path.insert(0,"./")
import smodels
print ( f"smodels {smodels.__file__}" )
from smodels.tools.printers.pythonPrinter import PyPrinter
from smodels_utils.helper.terminalcolors import *

# theoryPrediction.writeYields[0]=True

def addErrorsForRValuesMonkeyPatchFull ( self, obj, resDict : dict ):
    """ even more info, for debugging
    monkey patch to also report the observed
    see PyPrinter.addErrorsForRValues (and we need to keep them in sync
    manually)
    """
    print ( )
    print ( f"for {obj.dataset.globalInfo.id}: {obj.statsComputer}" )
    from smodels.statistics.basicStats import aposteriori, apriori
    nll_0 = obj.nll ( mu=0. )
    offset = nll_0
    print ( f"nll_0={nll_0:.3f}" )
    nll = obj.nll ( )
    print ( f"nll={nll:.3f}" )
    dnll = nll - nll_0
    print ( f"{GREEN}dnll={dnll:.3f}{RESET}" )
    d_nll_min = obj.nll_min ( return_dict = True )
    nll_min = d_nll_min["nll_min"] 
    mu_hat = d_nll_min["muhat"]
    # offset = nll_min
    print ( f"nll_min={nll_min:.3f} mu_hat={mu_hat:.3f}" )
    dnll_min = nll_min - nll_0
    print ( f"{GREEN}dnll_min={dnll_min:.3f}{RESET}" )
    nllA0 = obj.nll ( mu=0, asimov = 0 )
    print ( f"nllA0={nllA0:.3f}" )
    nllA = obj.nll ( mu=1, asimov = 0 )
    print ( f"nllA={nllA:.3f}" )
    dnllA = nllA - nllA0
    print ( f"{GREEN}dnllA={dnllA:.3f}{RESET}" )
    nll_posteriori_0 = obj.nll ( mu=0, evaluationType = aposteriori )
    print ( f"nll_posteriori_0={nll_posteriori_0:.3f}" )
    nll_posteriori = obj.nll ( mu=1, evaluationType = aposteriori )
    print ( f"nll_posteriori_1={nll_posteriori:.3f}" )
    dnll_posteriori = nll_posteriori - nll_posteriori_0
    print ( f"{GREEN}dnll_posteriori={dnll_posteriori:.3f}{RESET}" )
    dnllA = obj.nll ( asimov=0 )  - offset
    dnllE = obj.nll ( mu=1, evaluationType = aposteriori ) - offset
    d_posteriori_min = obj.nll_min ( evaluationType = aposteriori,
                                     return_dict = True )
    nll_posteriori_min = d_posteriori_min["nll_min"]
    mu_hat_posteriori = d_posteriori_min["muhat"]
    print ( f"nll_posteriori_min={nll_posteriori_min:.3f} muhat {mu_hat_posteriori:.3f}" )
    dnll_posteriori_min = nll_posteriori_min - nll_posteriori_0
    print ( f"{GREEN}dnll_posteriori_min={dnll_posteriori_min:.3f}{RESET}" )
    nll_priori_0 = obj.nll ( mu=0, evaluationType = apriori )
    print ( f"nll_priori_0={nll_priori_0:.3f}" )
    nll_priori = obj.nll ( mu=1, evaluationType = apriori )
    print ( f"nll_priori={nll_priori:.3f}" )
    dnll_priori = nll_priori - offset
    print ( f"{GREEN}dnll_priori={dnll_priori:.3f}{RESET}" )
    # nll_minA = obj.nll_min ( asimov = 1 )
    dnllEpriori = obj.nll ( evaluationType = apriori ) - offset
    dnllEA = obj.nll ( asimov=0, evaluationType = aposteriori ) - offset

    CLs = obj.CLs ( mu=1 )
    print ( f"CLs {CLs:.3f}" )
    """
    CLs0 = obj.CLs ( mu=0 )
    nllea0 = obj.nll ( mu=0, evaluationType=aposteriori, asimov=0 )
    print ( f"nllea0={nllea0:.3f}" )
    nllea = obj.nll ( mu=1, evaluationType=aposteriori, asimov=0 )
    print ( f"nllea={nllea:.3f}" )
    """
    CLs_posteriori = obj.CLs ( mu=1, evaluationType = aposteriori )
    print ( f"CLs_posteriori {CLs_posteriori:.5f}" )
    """
    CLsEpriori = obj.CLs ( mu=1, evaluationType = apriori )
    # nll_min = 0.
    resDict['CLs1']=CLs
    resDict['CLs0']=CLs0
    resDict['CLs_posteriori']=CLs_posteriori
    resDict['CLsEpriori']=CLsEpriori
    resDict['dnllA']=dnllA
    resDict['dnllE']=dnllE
    resDict['dnll_posteriori_min']=dnll_posteriori_min
    resDict['nll_min']=0.
    resDict['dnll']=dnll
    dnll_SM = 0.
    resDict['dnll_SM']=dnll_SM
    # resDict['nll_minA']=nll_minA
    resDict['dnllEpriori']=dnllEpriori
    resDict['dnllEA']=dnllEA
    r_e_p1 = obj.getRValue ( evaluationType = self.getTypeOfExpected(),
            nSigma = 1 )
    if r_e_p1 != None:
        resDict['r_expected_p1'] = self._round ( r_e_p1 )
    r_e_m1 = obj.getRValue ( evaluationType = self.getTypeOfExpected(),
            nSigma = -1 )
    if r_e_m1 != None:
        resDict['r_expected_m1'] = self._round ( r_e_m1 )
    # add only for expected
    from smodels.statistics.basicStats import observed
    r_obs_p1 = obj.getRValue ( evaluationType = observed, pmSigma = 1 )
    r_obs_m1 = obj.getRValue ( evaluationType = observed, pmSigma = -1 )
    if r_obs_p1 != None:
         resDict['r_nn_p1'] = self._round ( r_obs_p1 )
    if r_obs_m1 != None:
         resDict['r_nn_m1'] = self._round ( r_obs_m1 )
    """

PyPrinter.addErrorsForRValues = addErrorsForRValuesMonkeyPatchFull
from smodels.tools.runSModelS import main
main()
