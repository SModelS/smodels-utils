#!/usr/bin/env python3

"""
.. module:: pyhfInterface
   :synopsis: Code that delegates the computation of limits and likelihoods to
              pyhf.

.. moduleauthor:: Gael Alguero <gaelalguero@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
# [[SRA_L, SRA_M, SRA_H], [SRB], [SRC_22, SRC_24, SRC_26, SRC_28]]
from __future__ import print_function
import json
import jsonpatch
import pyhf
pyhf.set_backend(b"pytorch")
from scipy import optimize
import numpy as np

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

logger=getLogger()

class PyhfData:
    def __init__ (self, efficiencies, lumi, inputJsons):
        self.efficiencies = efficiencies
        logger.debug("Efficiencies : {}".format(efficiencies))
        self.lumi = lumi # fb
        self.inputJsons = inputJsons

class PyhfUpperLimitComputer:
    def __init__ ( self, data, cl=0.95):
        self.data = data
        self.nsignals = [self.data.lumi*1E3*eff for eff in self.data.efficiencies] # 1E3 rescaling so that mu matches a cross-section upper limit in pb
        logger.debug("Signals : {}".format(self.nsignals))
        self.inputJsons = self.data.inputJsons
        self.patches = self.patchMaker()
        self.workspaces = self.wsMaker()
        self.cl = cl
        self.scale = 1.

    def rescale(self, scale):
        """
        Rescales the signal predictions (self.signals) and processes again the patches and workspaces
        No return
        Result:
            updated list of patches and workspaces (self.patches and self.workspaces)
        """
        self.nsignals = [sig*scale for sig in self.nsignals]
        self.scale *= scale
        logger.debug("Signals : {}".format(self.nsignals))
        self.patches = self.patchMaker()
        self.workspaces = self.wsMaker()

    def patchMaker(self):
        """
        Method that creates the patches to be applied to the BkgOnly.json workspaces, one for each region
        It seems we need to include the change of the "modifiers" in the patches as well
        Returns:
            the list of patches, one for each workspace
        """
        nsignals = self.nsignals
        # Identifying the path of the SR and VR channels in the main workspace files
        ChannelsInfo = [] # workspace specifications
        self.zeroSignalsFlag = [] # One flag for each workspace
        for ws in self.inputJsons:
            self.zeroSignalsFlag.append(False)
            wsChannelsInfo = {}
            wsChannelsInfo["SR"] = []
            wsChannelsInfo["CRVR"] = []
            for i_ch, ch in enumerate(ws['channels']):
                if 'SR' in ch['name']:
                    logger.debug("SR channel name : %s" % ch['name'])
                    wsChannelsInfo['SR'].append({'path':'/channels/'+str(i_ch)+'/samples/0', # Path of the new sample to add (signal prediction)
                                                                         'size':len(ch['samples'][0]['data'])}) # Number of bins
                if 'VR' in ch['name'] or 'CR' in ch['name']:
                    wsChannelsInfo['CRVR'].append('/channels/'+str(i_ch))
            wsChannelsInfo["CRVR"].sort(key=lambda path: path.split('/')[-1], reverse=True) # Need to sort correctly the paths to the channels to be removed
            ChannelsInfo.append(wsChannelsInfo)
        # Constructing the patches to be applied on the main workspace files
        i_ws = 0
        patches = []
        for ws, info in zip(self.inputJsons, ChannelsInfo):
            # Need to read the number of SR/bins of each regions
            # in order to identify the corresponding ones in self.nsignals
            patch = []
            for sr in info['SR']:
                nSR = sr['size']
                operator = {}
                operator["op"] = "add"
                operator["path"] = sr['path']
                value = {}
                value["data"] = nsignals[:nSR]
                if value["data"] == [0 for x in range(nSR)]:
                    self.zeroSignalsFlag[i_ws] = True
                nsignals = nsignals[nSR:]
                value["modifiers"] = []
                value["modifiers"] .append({"data": None, "type": "normfactor", "name": "mu_SIG"})
                value["modifiers"] .append({"data": None, "type": "lumi", "name": "lumi"})
                value["name"] = "bsm"
                operator["value"] = value
                patch.append(operator)
            for path in info['CRVR']:
                patch.append({'op':'remove', 'path':path})
            patches.append(patch)
            i_ws += 1
        return patches

    def wsMaker(self):
        """
        Apply each region patch to his associated json (RegionN/BkgOnly.json) to obtain the complete workspaces
        Returns:
            the list of patched workspaces
        """
        if len(self.inputJsons) == 1:
            return [pyhf.Workspace(jsonpatch.apply_patch(self.inputJsons[0], self.patches[0]))]
        else:
            workspaces = []
            for json, patch in zip(self.inputJsons, self.patches):
                wsDict = jsonpatch.apply_patch(json, patch)
                ws = pyhf.Workspace(wsDict)
                workspaces.append(ws)
            return workspaces

    # Trying a new method for upper limit computation :
    # re-scaling the signal predictions so that mu falls in [0, 10] instead of looking for mu bounds
    # Usage of the index allows for rescaling
    def ulSigma (self, expected=False, workspace_index=None):
        """
        Compute the upper limit on the signal strength modifier with:
            - by default, the combination of the workspaces contained into self.workspaces
            - if workspace_index is specified, self.workspace[workspace_index] (useful for computation of the best upper limit)
        Returns:
            the upper limit at `self.cl` level (0.95 by default)
        """
        if workspace_index != None and self.zeroSignalsFlag[workspace_index] == True:
            logger.warning("Workspace number %d has zero signals" % workspace_index)
            return -1
        def updateWorkspace():
            if workspace_index != None:
                return self.workspaces[workspace_index]
            else:
                return self.cbWorkspace()
        workspace = updateWorkspace()
        scale = 1.
        def root_func(mu):
            # Same modifiers_settings as those use when running the 'pyhf cls' command line
            msettings = {'normsys': {'interpcode': 'code4'}, 'histosys': {'interpcode': 'code4p'}}
            model = workspace.model(modifier_settings=msettings)
            test_poi = mu
            result = pyhf.infer.hypotest(test_poi, workspace.data(model), model, qtilde=True, return_expected = expected)
            if expected:
                CLs = result[1].tolist()[0]
            else:
                CLs = result[0]
            logger.info("Call of root_func(%f) -> %f" % (mu, 1.0 - CLs))
            return 1.0 - self.cl - CLs
        # Checking if the lower limit gives a nan, in which case the signal needs to be scaled up
        # while np.isnan(root_func(1.)):
            # self.rescale(2.)
            # workspace = updateWorkspace()
        # # Scaling the signal prediction
        # while root_func(10.) < 0.0:
            # # Scaling up the signals and updating the workspace
            # self.rescale(2.)
            # workspace = updateWorkspace()
        # while root_func(1.) > 0.0:
            # # Scaling down the signals and updating the workspace
            # self.rescale(0.5)
            # workspace = updateWorkspace()
        # Trying a more advanced method for rescaling
        factor = .2
        wereBothLarge = False
        wereBothTiny = False
        while "mu is not in [0,10]":
            # Computing CL(1) - 0.95 and CL(10) - 0.95 once and for all
            rt1 = root_func(1.)
            rt10 = root_func(10.)
            if rt1 < 0. and 0. < rt10: # Here's the real while condition
                break
            if np.isnan(rt1):
                self.rescale(1+factor)
                workspace = updateWorkspace()
                continue
            if np.isnan(rt10):
                self.rescale(1-factor)
                workspace = updateWorkspace()
                continue
            # Analyzing previous values of wereBoth***
            if rt10 < 0 and rt1 < 0 and wereBothLarge:
                factor = factor/2
                logger.info("Diminishing rescaling factor")
            if rt10 > 0 and rt1 > 0 and wereBothTiny:
                factor = factor/2
                logger.info("Diminishing rescaling factor")
            # Preparing next values of wereBoth***
            wereBothTiny = rt10 < 0 and rt1 < 0
            wereBothLarge = rt10 > 0 and rt1 > 0
            if rt10 < 0.:
                self.rescale(1+factor)
                workspace = updateWorkspace()
                continue
            if rt1 > 0.:
                self.rescale(1-factor)
                workspace = updateWorkspace()
                continue
        # Finding the root (Brent bracketing part)
        logger.info("Final scale : %f" % self.scale)
        hi_mu = 10.
        lo_mu = 1.
        logger.info("Starting brent bracketing")
        ul = optimize.brentq(root_func, lo_mu, hi_mu, rtol=1e-3, xtol=1e-3)
        return ul*self.scale # self.scale has been updated whithin self.rescale() method

    def bestUL(self):
        """
        Computing the upper limit on the signal strength modifier in the expected hypothesis for each workspace
        Picking the most sensitive, i.e., the one having the biggest r-value in the expected case (r-value = 1/mu)
        """
        if len(self.workspaces) == 1:
            return self.ulSigma(workspace_index=0)
        rMax = 0.0
        for i_ws in range(len(self.workspaces)):
            logger.info("Looking for best expected combination")
            r = 1/self.ulSigma(expected=True, workspace_index=i_ws)
            if r > rMax:
                rMax = r
                i_best = i_ws
        logger.info('Best combination : %d' % i_best)
        return self.ulSigma(workspace_index=i_best)

    def cbWorkspace(self):
        """
        Method that combines the workspaces contained in the workspaces list into a single workspace
        """
        # Performing combination using pyhf.workspace.combine method, a bit modified to solve the multiple parameter configuration problem
        workspaces = self.workspaces
        if len(workspaces) == 1:
            cbWS = workspaces[0]
        for i_ws in range(len(workspaces)):
            if self.zeroSignalsFlag[i_ws] == False:
                cbWS = workspaces[i_ws]
                break
        for i_ws in range(1, len(workspaces)):
            if self.zeroSignalsFlag[i_ws] == True: # Ignore workspaces having zero signals
                continue
            cbWS = pyhf.Workspace.combine(cbWS, workspaces[i_ws])
        # Home made method, should do the same but no sanity checks and the first measurement is taken:
        # cbWS = {}
        # cbWS["channels"] = []
        # for inpt in workspaces:
            # for channel in inpt["channels"]:
                # cbWS["channels"].append(channel)
        # cbWS["observations"] = []
        # for inpt in workspaces:
            # for observation in inpt["observations"]:
                # cbWS["observations"].append(observation)
        # cbWS["measurements"] = workspaces[0]["measurements"]
        # cbWS["version"] = workspaces[0]["version"]
        # These two last are assumed to be the same for all three regions
        return cbWS

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
