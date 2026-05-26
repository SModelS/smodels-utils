#!/usr/bin/env python3

import sys
sys.path.insert(0,"../smodels-utils/")
sys.path.insert(0,"../smodels-utils/validation/")
from smodels.tools.printers.pythonPrinter import PyPrinter

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
    nllA = obj.nll ( asimov=1 )
    nllE = obj.nll ( mu=1, evaluationType = aposteriori )
    nllEpriori = obj.nll ( evaluationType = apriori )
    nllEA = obj.nll ( asimov=1, evaluationType = aposteriori )
    resDict['CLs1']=CLs
    resDict['CLs0']=CLs0
    resDict['CLsE']=CLsE
    resDict['nllA']=nllA
    resDict['nllE']=nllE
    resDict['nllEpriori']=nllEpriori
    resDict['nllEA']=nllEA
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
