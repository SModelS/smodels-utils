#!/usr/bin/env python3

"""
.. module:: pyhfInterface
   :synopsis: Code that delegates the computation of limits and likelihoods to
              pyhf.

.. moduleauthor:: Gael Alguero <gaelalguero@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
from __future__ import print_function
import json
import jsonpatch
import pyhf
pyhf.set_backend(b"pytorch")
from scipy import optimize
import numpy as np
from smodels.base.smodelsLogging import logger
import time

def getLogger():
    """
    Configure the logging facility. Maybe adapted to fit into
    your framework.
    """

    import logging

    logger = logging.getLogger("pyhfInterface")
    # formatter = logging.Formatter('%(module)s - %(levelname)s: %(message)s')
    # ch = logging.StreamHandler()
    # ch.setFormatter(formatter)
    # ch.setLevel(logging.DEBUG)
    # logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    return logger

#logger=getLogger()

class PyhfData:
    """
    Holds data for use in pyhf
    :ivar nsignals: signal predictions list divided into sublists, one for each json file
    :ivar inputJsons: list of json instances
    :ivar nWS: number of workspaces = number of json files
    """
    def __init__ (self, nsignals, inputJsons):
        self.nsignals = nsignals # fb
        self.inputJsons = inputJsons
        self.nWS = len(inputJsons)
        self.errorFlag = False
        self.getWSInfo()
        self.checkConsistency()

    def getWSInfo(self):
        """
        Getting informations from the json files

        :ivar channelsInfo: list of dictionaries (one dictionary for each json file) containing useful information about the json files
            - :key signalRegions: list of dictonaries with 'json path' and 'size' (number of bins) of the 'signal regions' channels in the json files
            - :key otherRegions: list of strings indicating the path to the control and validation region channels
        """
        # Identifying the path to the SR and VR channels in the main workspace files
        self.channelsInfo = [] # workspace specifications
        if not isinstance(self.inputJsons, list):
            logger.error("The `inputJsons` parameter must be of type list")
            self.errorFlag = True
            return
        for ws in self.inputJsons:
            wsChannelsInfo = {}
            wsChannelsInfo['signalRegions'] = []
            wsChannelsInfo['otherRegions'] = []
            if not 'channels' in ws.keys():
                logger.error(f"Json file number {self.inputJsons.index(ws)} is corrupted (channels are missing)")
                self.channelsInfo = None
                return
            for i_ch, ch in enumerate(ws['channels']):
                if 'SR' in ch['name']:
                    wsChannelsInfo['signalRegions'].append({'path':'/channels/'+str(i_ch)+'/samples/0', # Path of the new sample to add (signal prediction)
                                                            'size':len(ch['samples'][0]['data'])}) # Number of bins
                if 'VR' in ch['name'] or 'CR' in ch['name']:
                    wsChannelsInfo['otherRegions'].append('/channels/'+str(i_ch))
            wsChannelsInfo['otherRegions'].sort(key=lambda path: path.split('/')[-1], reverse=True) # Need to sort correctly the paths to the channels to be removed
            self.channelsInfo.append(wsChannelsInfo)

    def checkConsistency(self):
        """
        Check various inconsistencies of the PyhfData attributes

        :ivar zeroSignalsFlag: boolean identifying if all SRs of a single json are empty
        """
        if not isinstance(self.nsignals, list):
            logger.error("The `nsignals` parameter must be of type list")
            self.errorFlag = True
        if self.nWS != len(self.nsignals):
            logger.error('The number of subsignals provided is different from the number of json files')
            self.errorFlag = True
        self.zeroSignalsFlag = list()
        if self.channelsInfo == None:
            return
        for wsInfo, subSig in zip(self.channelsInfo, self.nsignals):
            if not isinstance(subSig, list):
                logger.error("The `nsignals` parameter must be a two dimensional list")
                self.errorFlag = True
            nBinsJson = 0
            for sr in wsInfo['signalRegions']:
                nBinsJson += sr['size']
            if nBinsJson != len(subSig):
                logger.error(f'The number of signals provided is different from the number of bins for json number {self.channelsInfo.index(wsInfo)} and channel number {self.nsignals.index(subSig)}')
                self.errorFlag = True
            allZero = all([s == 0 for s in subSig])
            # Checking if all signals matching this json are zero
            self.zeroSignalsFlag.append(allZero)

class PyhfUpperLimitComputer:
    """
    Class that computes the upper limit using the jsons files and signal informations in the `data` instance of `PyhfData`
    """
    def __init__ ( self, data, cl=0.95):
        """
        :param: data: instance of `PyhfData` holding the signals information
        :param cl: confdence level at which the upper limit is desired to be computed

        :ivar data: created from :param data:
        :ivar nsignals: signal predictions list divided into sublists, one for each json file
        :ivar inputJsons: list of input json files as python json instances
        :ivar channelsInfo: list of channels information for the json files
        :ivar zeroSignalsFlag: list boolean flags in case all signals are zero for a specific json
        :ivar nWS: number of workspaces = number of json files
        :ivar patches: list of patches to be applied to the inputJsons as python dictionary instances
        :ivar workspaces: list of workspaces resulting from the patched inputJsons
        :ivar cl: created from :param cl:
        :ivar scale: scale that is applied to the signal predictions, dynamically changes throughout the upper limit calculation
        :ivar alreadyBeenThere: boolean flag that identifies when the :ivar nsignals: accidentally passes twice at two identical values
        """
        self.data = data
        self.nsignals = self.data.nsignals
        logger.debug(f"Signals : {self.nsignals}")
        self.inputJsons = self.data.inputJsons
        self.channelsInfo = self.data.channelsInfo
        self.zeroSignalsFlag = self.data.zeroSignalsFlag
        self.nWS = self.data.nWS
        self.patches = self.patchMaker()
        self.workspaces = self.wsMaker()
        self.cl = cl
        self.scale = 1.
        self.alreadyBeenThere = False # boolean to detect wether self.signals has returned to an older value

    def rescale(self, factor):
        """
        Rescales the signal predictions (self.nsignals) and processes again the patches and workspaces

        :return: updated list of patches and workspaces (self.patches and self.workspaces)
        """
        self.nsignals = [[sig*factor for sig in ws] for ws in self.nsignals]
        try:
            self.alreadyBeenThere = self.nsignals == self.nsignals_2
        except AttributeError:
            pass
        self.scale *= factor
        self.patches = self.patchMaker()
        self.workspaces = self.wsMaker()
        try:
            self.nsignals_2 = self.nsignals_1.copy() # nsignals at previous-to-previous loop
        except AttributeError:
            pass
        self.nsignals_1 = self.nsignals.copy() # nsignals at previous loop

    def patchMaker(self):
        """
        Method that creates the list of patches to be applied to the `self.inputJsons` workspaces, one for each region given the `self.nsignals` and the informations available in `self.channelsInfo` and the content of the `self.inputJsons`
        NB: It seems we need to include the change of the "modifiers" in the patches as well

        :return: the list of patches, one for each workspace
        """
        if self.channelsInfo == None:
            return None
        nsignals = self.nsignals
        # Constructing the patches to be applied on the main workspace files
        patches = []
        for ws, info, subSig in zip(self.inputJsons, self.channelsInfo, self.nsignals):
            patch = []
            for srInfo in info['signalRegions']:
                nBins = srInfo['size']
                operator = {}
                operator["op"] = "add"
                operator["path"] = srInfo['path']
                value = {}
                value["data"] = subSig[:nBins]
                subSig = subSig[nBins:]
                value["modifiers"] = []
                value["modifiers"].append({"data": None, "type": "normfactor", "name": "mu_SIG"})
                value["modifiers"].append({"data": None, "type": "lumi", "name": "lumi"})
                value["name"] = "bsm"
                operator["value"] = value
                patch.append(operator)
            for path in info['otherRegions']:
                patch.append({'op':'remove', 'path':path})
            patches.append(patch)
        return patches

    def wsMaker(self):
        """
        Apply each region patch (self.patches) to his associated json (self.inputJsons) to obtain the complete workspaces

        :returns: the list of patched workspaces
        """
        if self.patches == None:
            return None
        if self.nWS == 1:
            try:
                return [pyhf.Workspace(jsonpatch.apply_patch(self.inputJsons[0], self.patches[0]))]
            except (pyhf.exceptions.InvalidSpecification, KeyError) as e:
                logger.error(f"The json file is corrupted:\n{e}")
                return None
        else:
            workspaces = []
            for js, patch in zip(self.inputJsons, self.patches):
                wsDict = jsonpatch.apply_patch(js, patch)
                try:
                    ws = pyhf.Workspace(wsDict)
                except (pyhf.exceptions.InvalidSpecification, KeyError) as e:
                    logger.error(f"Json file number {self.inputJsons.index(json)} is corrupted:\n{e}")
                    return None
                workspaces.append(ws)
            return workspaces

    def likelihood(self, workspace_index=None):
        """
        Returns the value of the likelihood.
        Inspired by the `pyhf.infer.mle` module but for non-log likelihood
        """
        logger.debug("Calling likelihood")
        self.scale = 1.
        if self.nWS == 1:
            workspace = self.workspaces[0]
        elif workspace_index != None:
            if self.zeroSignalsFlag[workspace_index] == True:
                logger.warning("Workspace number %d has zero signals" % workspace_index)
                return None
            else:
                workspace = self.workspaces[workspace_index]
        else:
            workspace = self.cbWorkspace()
        # Same modifiers_settings as those use when running the 'pyhf cls' command line
        msettings = {'normsys': {'interpcode': 'code4'}, 'histosys': {'interpcode': 'code4p'}}
        model = workspace.model(modifier_settings=msettings)
        test_poi = 1.
        _, nllh = pyhf.infer.mle.fixed_poi_fit(test_poi, workspace.data(model), model, return_fitted_val=True)
        nl =  self.tofloat ( nllh ) ## convert to float
        return np.exp(-nl/2)

    def tofloat ( self, tensor ):
        """ retrieve a float out of a tensor with a single entry.
            make sure it works with all backends and versions """
        try:
            number = float(tensor)
            return number
        except:
            pass
        number = tensor[0]
        return number


    def chi2(self, workspace_index=None):
        """
        Returns the chi square
        """
        self.scale = 1.
        logger.debug("Calling chi2")
        return None

    # Trying a new method for upper limit computation :
    # re-scaling the signal predictions so that mu falls in [0, 10] instead of looking for mu bounds
    # Usage of the index allows for rescaling
    def ulSigma (self, expected=False, workspace_index=None):
        """
        Compute the upper limit on the signal strength modifier with:
            - by default, the combination of the workspaces contained into self.workspaces
            - if workspace_index is specified, self.workspace[workspace_index] (useful for computation of the best upper limit)

        :param expected:  - if set to `True`: uses expected SM backgrounds as signals
                          - else: uses `self.nsignals`
        :param workspace_index: - if different from `None`: index of the workspace to use for upper limit
                          - else: all workspaces are combined
        :return: the upper limit at `self.cl` level (0.95 by default)
        """
        startUL = time.time()
        logger.debug("Calling ulSigma")
        if self.data.errorFlag or self.workspaces == None: # For now, this flag can only be turned on by PyhfData.checkConsistency
            return None
        if self.nWS == 1:
            if self.zeroSignalsFlag[0] == True:
                logger.warning("There is only one workspace but all signals are zeroes")
                return None
        else:
            if workspace_index == None:
                logger.error("There are several workspaces but no workspace index was provided")
                return None
            elif self.zeroSignalsFlag[workspace_index] == True:
                logger.debug("Workspace number %d has zero signals" % workspace_index)
                return None
        def updateWorkspace():
            if self.nWS == 1:
                return self.workspaces[0]
            else:
                return self.workspaces[workspace_index]
        workspace = updateWorkspace()
        def root_func(mu):
            # Same modifiers_settings as those use when running the 'pyhf cls' command line
            msettings = {'normsys': {'interpcode': 'code4'}, 'histosys': {'interpcode': 'code4p'}}
            model = workspace.model(modifier_settings=msettings)
            test_poi = mu
            start = time.time()
            result = pyhf.infer.hypotest(test_poi, workspace.data(model), model, qtilde=True, return_expected = expected)
            end = time.time()
            logger.debug(f"Hypotest elapsed time : {end - start:1.4f} secs")
            if expected:
                logger.debug(f"expected = {expected}, mu = {mu}, result = {result}")
                CLs = float(result[1].tolist()[0])
            else:
                logger.debug(f"expected = {expected}, mu = {mu}, result = {result}")
                CLs = float(result[0])
            # logger.debug("Call of root_func(%f) -> %f" % (mu, 1.0 - CLs))
            return 1.0 - self.cl - CLs
        # Rescaling singals so that mu is in [0, 10]
        factor = 10.
        wereBothLarge = False
        wereBothTiny = False
        while "mu is not in [0,10]":
            # Computing CL(1) - 0.95 and CL(10) - 0.95 once and for all
            rt1 = root_func(1.)
            rt10 = root_func(10.)
            if rt1 < 0. and 0. < rt10: # Here's the real while condition
                break
            if self.alreadyBeenThere:
                factor = 1 + (factor-1)/2
                logger.debug("Diminishing rescaling factor")
            if np.isnan(rt1):
                self.rescale(factor)
                workspace = updateWorkspace()
                continue
            if np.isnan(rt10):
                self.rescale(1/factor)
                workspace = updateWorkspace()
                continue
            # Analyzing previous values of wereBoth***
            if rt10 < 0 and rt1 < 0 and wereBothLarge:
                factor = 1 + (factor-1)/2
                logger.debug("Diminishing rescaling factor")
            if rt10 > 0 and rt1 > 0 and wereBothTiny:
                factor = 1 + (factor-1)/2
                logger.debug("Diminishing rescaling factor")
            # Preparing next values of wereBoth***
            wereBothTiny = rt10 < 0 and rt1 < 0
            wereBothLarge = rt10 > 0 and rt1 > 0
            # Main rescaling code
            if rt10 < 0.:
                self.rescale(factor)
                workspace = updateWorkspace()
                continue
            if rt1 > 0.:
                self.rescale(1/factor)
                workspace = updateWorkspace()
                continue
        # Finding the root (Brent bracketing part)
        logger.debug(f"Final scale : {self.scale:f}")
        hi_mu = 10.
        lo_mu = 1.
        logger.debug("Starting brent bracketing")
        ul = optimize.brentq(root_func, lo_mu, hi_mu, rtol=1e-3, xtol=1e-3)
        endUL = time.time()
        logger.debug(f"ulSigma elpased time : {endUL - startUL:1.4f} secs")
        return ul*self.scale # self.scale has been updated whithin self.rescale() method

if __name__ == "__main__":
    C = [ 18774.2, -2866.97, -5807.3, -4460.52, -2777.25, -1572.97, -846.653, -442.531,
       -2866.97, 496.273, 900.195, 667.591, 403.92, 222.614, 116.779, 59.5958,
       -5807.3, 900.195, 1799.56, 1376.77, 854.448, 482.435, 258.92, 134.975,
       -4460.52, 667.591, 1376.77, 1063.03, 664.527, 377.714, 203.967, 106.926,
       -2777.25, 403.92, 854.448, 664.527, 417.837, 238.76, 129.55, 68.2075,
       -1572.97, 222.614, 482.435, 377.714, 238.76, 137.151, 74.7665, 39.5247,
       -846.653, 116.779, 258.92, 203.967, 129.55, 74.7665, 40.9423, 21.7285,
       -442.531, 59.5958, 134.975, 106.926, 68.2075, 39.5247, 21.7285, 11.5732]
    nsignal = [ x/100. for x in [47,29.4,21.1,14.3,9.4,7.1,4.7,4.3] ]
    m=Data( observed=[1964,877,354,182,82,36,15,11],
              backgrounds=[2006.4,836.4,350.,147.1,62.0,26.2,11.1,4.7],
              covariance= C,
#              third_moment = [ 0.1, 0.02, 0.1, 0.1, 0.003, 0.0001, 0.0002, 0.0005 ],
              third_moment = [ 0. ] * 8,
              nsignal = nsignal,
              name="ATLAS-SUSY-2018-31 model" )
    ulComp = PyhfUpperLimitComputer(cl=.95)
    #uls = ulComp.ulSigma ( Data ( 15,17.5,3.2,0.00454755 ) )
    #print ( "uls=", uls )
    ul_old = 131.828*sum(nsignal) #With respect to the older refernece value one must normalize the xsec
    print ( "old ul=", ul_old )
    ul = ulComp.ulSigma ( m )
    print ( "ul (marginalized)", ul )
    ul = ulComp.ulSigma ( m, marginalize=False )
    print ( "ul (profiled)", ul )
