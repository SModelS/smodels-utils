#!/usr/bin/env python3

import sys
sys.path.insert(0,"../smodels-utils/")
sys.path.insert(0,"../smodels-utils/validation/")
sys.path.insert(0,"./")
import smodels
print ( f"smodels {smodels.__file__}" )
from smodels.tools.printers.pythonPrinter import PyPrinter
from smodels.matching import theoryPrediction

# theoryPrediction.writeYields[0]=True

def addErrorsForRValuesMonkeyPatchFull ( self, obj, resDict : dict ):
    """ even more info, for debugging
    monkey patch to also report the observed
    see PyPrinter.addErrorsForRValues (and we need to keep them in sync
    manually)
    """
    from smodels.statistics.basicStats import aposteriori, apriori
    CLs = obj.CLs ( mu=1 )
    CLs0 = obj.CLs ( mu=0 )
    CLsE = obj.CLs ( mu=1, evaluationType = aposteriori )
    CLsEpriori = obj.CLs ( mu=1, evaluationType = apriori )
    nll_min = obj.nll_min ( )
    offset = nll_min
    dnll = obj.nll ( ) - offset
    dnll_SM = obj.nll ( mu=0. ) - offset
    nll_min = 0.
    dnllA = obj.nll ( asimov=1 )  - offset
    dnllE = obj.nll ( mu=1, evaluationType = aposteriori ) - offset
    dnll_minE = obj.nll_min ( evaluationType = aposteriori ) - offset
    # nll_minA = obj.nll_min ( asimov = 1 )
    dnllEpriori = obj.nll ( evaluationType = apriori ) - offset
    dnllEA = obj.nll ( asimov=1, evaluationType = aposteriori ) - offset
    resDict['CLs1']=CLs
    resDict['CLs0']=CLs0
    resDict['CLsE']=CLsE
    resDict['CLsEpriori']=CLsEpriori
    resDict['dnllA']=dnllA
    resDict['dnllE']=dnllE
    resDict['dnll_minE']=dnll_minE
    resDict['nll_min']=0.
    resDict['dnll']=dnll
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

PyPrinter.addErrorsForRValues = addErrorsForRValuesMonkeyPatchFull
from smodels.tools.runSModelS import main
main()
