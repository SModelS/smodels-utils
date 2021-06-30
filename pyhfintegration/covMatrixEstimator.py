#!/usr/bin/env python3

"""
.. module:: covMatrixEstimator
   :synopsis: a tool to get the covariance matrix out of a pyhf likelihood

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import cabinetry
import pyhf
import pickle, os, subprocess
import numpy as np

class CovMatrixEstimator ( object ):
    def __init__ ( self, anaid ):
        pyhf.set_backend("numpy", pyhf.optimize.minuit_optimizer(verbose=1))
        self.anaid = anaid
        self.jsonfile = "example.json"
        self.nsamples = 200000
        self.toStore = [ "yields", "yield_unc", "ncov", "model", "channels", "data",
                         "corr", "nsamples" ]
        #                 "result", "result_obj" ]

    def get_channel_boundary_indices(self):
        """Returns indices for splitting a concatenated list of observations into channels.
        This is useful in combination with ``pyhf.pdf.Model.expected_data``, which returns
        the yields across all bins in all channels. These indices mark the positions where a
        channel begins. No index is returned for the first channel, which begins at ``[0]``.
        The returned indices can be used with ``numpy.split``.
        Returns:
            List[int]: indices of positions where a channel begins, no index is included for
            the first bin of the first channel (which is always at ``[0]``)
        """
        # get the amount of bins per channel
        bins_per_channel = [self.model.config.channel_nbins[ch] for ch in self.model.config.channels]
        # indices of positions where a new channel starts (from the second channel onwards)
        channel_start = [sum(bins_per_channel[:i]) for i in range(1, len(bins_per_channel))]
        return channel_start

    def pprint ( self, *args ):
        """ logging """
        print ( "[covMatrixEstimator] %s" % (" ".join(map(str,args))) )

    def download( self, force=False ):
        hepdataids = { "ATLAS-SUSY-2018-04": 1406212, "ATLAS-SUSY-2018-06": 1404698,
                       "ATLAS-SUSY-2019-08": 1934827, "ATLAS-SUSY-2018-31": 1935437 }
        hepdataid = hepdataids[self.anaid]
        import os, subprocess
        if os.path.exists ( self.jsonfile ) and not force:
            return
        from pyhf.contrib import utils
        url = f"https://www.hepdata.net/record/resource/{hepdataid}?view=true"
        shortanaid = self.anaid.replace("ATLAS-","")
        Dir = shortanaid+"_likelihoods/"
        self.pprint ( f"downloading {hepdataid} to {Dir}" )
        utils.download( url, Dir )
        return

    def patch ( self ):
        patchcmds = {}
        patchcmds["ATLAS-SUSY-2018-04"] = "jsonpatch @@Dir@@/Region-combined/BkgOnly.json @@Dir@@/Region-combined/test.json"
        patchcmds["ATLAS-SUSY-2018-06"] = 'jsonpatch @@Dir@@/BkgOnly.json <(pyhf patchset extract @@Dir@@/patchset.json --name "ERJR_500p0_300p0")'
        patchcmds["ATLAS-SUSY-2018-31"] = 'jsonpatch @@Dir@@/RegionC/BkgOnly.json <(pyhf patchset extract @@Dir@@/RegionC/patchset.json --name "sbottom_1300_1050_60")'
        patchcmds["ATLAS-SUSY-2019-08"] = 'jsonpatch @@Dir@@/BkgOnly.json <(pyhf patchset extract @@Dir@@/patchset.json --name "C1N2_Wh_hbb_700_400")'
        patchcmd = patchcmds[self.anaid]
        shortanaid = self.anaid.replace("ATLAS-","")
        Dir = shortanaid+"_likelihoods/"
        patchcmd = patchcmd.replace ( "@@Dir@@", Dir )

        cmd = f"{patchcmd} > {self.jsonfile}"
        self.pprint ( f"patching to {self.jsonfile}" )
        self.pprint ( cmd )
        tmpf = "./tmp.sh"
        with open ( tmpf, "wt" ) as f:
            f.write ( "#!/bin/bash\n\n" )
            f.write ( cmd+"\n" )
            f.close()
        os.chmod ( tmpf, 0o755 )
        o = subprocess.getoutput ( tmpf )
        if len(o)>1:
            self.pprint ( o ) 
        return

    def interact ( self ):
        import IPython
        IPython.embed( using = False )

    def store ( self ):
        """ save result to pickle """
        fname = f"{self.anaid}.pcl"
        if os.path.exists ( fname ):
            cmd = "cp {fname} {fname}.bu"
            subprocess.getoutput ( cmd )
        Dict = {}
        for label in self.toStore:
            Dict[label]=getattr(self,label)
        with open ( fname,"wb" ) as f:
            pickle.dump ( Dict, f )
            f.close()

    def load ( self ):
        """ load results from pickle """
        fname = f"{self.anaid}.pcl"
        if not os.path.exists ( fname ):
            self.pprint ( f"{fname} does not exist, will try and create" )
            self.retrieveMatrix()
            return self.store()

        with open ( fname,"rb" ) as f:
            Dict = pickle.load ( f )
            f.close()
        for k in self.toStore:
            if not k in Dict:
                continue
            self.__dict__[k]=Dict[k]

    def retrieveSubmatrix ( self, indices ):
        """ retrieve the sub covariance matrix for indices,
            e.g. (1,2,3) """
        if len(indices)==0:
            return []
        indices = np.array ( indices )
        scov = self.ncov[indices[:,None],indices]
        return scov

    def toCanonical ( self, channelname ):
        """ return canonical form of channelname """
        Dict = { "SRLMEM_mct2": "SR_LM_Low_MCT",
                 "SR_LM_High_MCT": "SRLMEM_mct2",
                 "SR_LM_Low_MCT": "SRLMEM_mct2" }
        if channelname in Dict:
            return Dict[channelname]
        return channelname


    def getChannelName ( self, binid, canonical=False ):
        """ get the name of the channel of bin <binid>
        :param canonical: if true, return a canonical form of name
        """
        indices = self.get_channel_boundary_indices()
        for i,idx in enumerate(indices):
            if binid < idx:
                ret = self.channels[i]
                if canonical:
                    ret = self.toCanonical ( ret )
                return ret

    def querySModelS ( self ):
        """ query the SModelS database for the order of the SRs """
        if hasattr ( self, "datasetIndices" ):
            self.pprint ( "SModelS info already retrieved" )
            return
        from smodels.experiment.databaseObj import Database
        db = Database ( "../../smodels-database/" )
        er = db.getExpResults ( analysisIDs = [ self.anaid ],
                dataTypes = [ "efficiencyMap" ], useNonValidated = True )
        if type(er) != list or len(er)<1:
            return
        datasets = er[0].datasets
        dsnames = [ x.dataInfo.dataId for x in datasets[:3] ]
        self.pprint ( "datasets:", ", ".join ( dsnames ),"..." )
        self.datasetIndices = {}
        self.dataIndexNames = {}
        oldNames = {}
        for ds in datasets:
            dsName = ds.dataInfo.dataId
            obsN = ds.dataInfo.observedN
            hadAMatch = False
            for i,d in enumerate(self.data):
                channelname = self.getChannelName(i,True)
                if abs ( obsN - d ) <1e-7:
                    namesMatch = False
                    if hadAMatch:
                        self.pprint ( f"{d} matches twice for {dsName} {channelname} -- old one was {oldNames[dsName]}" )
                        if "LM" in dsName and "LM" in channelname:
                            hadAMatch = False
                        if "MM" in dsName and "MM" in channelname:
                            hadAMatch = False
                    if not hadAMatch:
                        self.pprint ( f"{channelname} with {obsN} matching to {dsName}" )
                        self.datasetIndices[dsName] = i
                        self.dataIndexNames[i] = dsName
                        oldNames[dsName]=channelname
                        hadAMatch = True
        return #er[0].datasets

    def createSModelSInfo ( self, pprint = False ):
        """
        write out lines for smodels info
        :param pprint: if true, then align the cov matrix
        """
        self.querySModelS()
        line = "datasetOrder: "
        def addApostrophes ( strng ):
            return f'"{strng}"'
        keys = list ( self.dataIndexNames.keys() )
        keys.sort()
        #line += ", ".join ( [ self.dataIndexNames[k] for k in keys ] )
        line += ", ".join ( map ( addApostrophes, [ self.dataIndexNames[k] for k in keys ] ) )
        print ( line )
        print ( "retrieving submatrix for", keys )
        matrix = self.retrieveSubmatrix ( keys )
        smatrix = "covariance: ["
        appendix = ", "
        if pprint:
            appendix = ",\n             "
        row=[]
        for row in matrix:
            smatrix += "["
            for col in row:
                if pprint:
                    smatrix += "%6.2f, " % col
                else:
                    smatrix += "%.3f, " % col
            if len(row)>0:
                smatrix = smatrix[:-2]
            # smatrix += "],\n             "
            smatrix += "]" + appendix
        if len(row)>0:
            nlast = -2
            if pprint:
                nlast = -14
            # smatrix = smatrix[:-14] + "]"
            smatrix = smatrix[:-2] + "]"

        print ( smatrix )

    def retrieveMatrix( self ):
        ws = cabinetry.workspace.load( self.jsonfile )
        model, data = cabinetry.model_utils.model_and_data(ws)
        channels = model.config.channels

        muSigIndex = model.config.parameters.index ( "mu_SIG" )
        suggestedBounds = model.config.suggested_bounds()
        suggestedBounds[muSigIndex]=(-10.,10.)

        result, result_obj = pyhf.infer.mle.fit(
                    data, model, return_uncertainties=True, return_result_obj=True,
                    par_bounds = suggestedBounds )

        self.result = result
        self.result_obj = result_obj

        # sample parameters from multivariate Gaussian and evaluate model
        sampled_parameters = np.random.multivariate_normal(
            result_obj.minuit.values, result_obj.minuit.covariance, size=self.nsamples )
        model_predictions = [
            model.expected_data(p, include_auxdata=False) for p in sampled_parameters
        ]

        for i,name in enumerate ( model.config.parameters ):
            fit = result_obj.minuit.values[i]
            bound = model.config.suggested_bounds()[i]
            if abs ( fit - bound[0] ) < 1e-5:
                print ( f"Fitted value {fit} of {name} hit bound {bound}" )
            if abs ( fit - bound[1] ) < 1e-5:
                print ( f"Fitted value {fit} of {name} hit bound {bound}" )

        yields = np.mean(model_predictions, axis=0)
        yield_unc = np.std(model_predictions, axis=0)
        self.model = model
        self.data = data
        self.channels = channels
        self.yields = yields
        self.yield_unc = yield_unc
        print(f"model predictions:\n" )
        for i,channel in enumerate ( channels ):
            print ( f" -- {channel}: {yields[i]:.2f}+/-{yield_unc[i]:.2f}" )

        np.set_printoptions ( precision = 3 )
        self.ncov = np.cov(model_predictions, rowvar=False)
        ncov = self.ncov
        self.corr = np.corrcoef(model_predictions, rowvar=False)
        #print(f"covariance:\n{ncov}")
        ## print(f"correlation:\n{np.corrcoef(model_predictions, rowvar=False)}")

        #scov = self.retrieveSubmatrix ( [2,3] )
        #print ( f"covariance of SRs (2,3):\n{scov}" )

        #scov = self.retrieveSubmatrix ( [1,3] )
        ### indices of signal regions
        #print ( f"covariance of SRs (1,3):\n{scov}" )
        #for i in indices.tolist():
        #    ncov[i][i]=ncov[i][i]-yields[i]
        #scov = ncov[indices[:,None],indices]
        #print ( f"covariance of SRs w/o Poissonian (1,3):\n{scov}" )
        #return scov.tolist()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SModelS-tools command line tool.")
    parser.add_argument('-w','--write', help='write pickle file', action="store_true" )
    parser.add_argument('-p','--patch', help='patch json file', action="store_true" )
    parser.add_argument('-d','--download', help='download json files', action="store_true" )
    parser.add_argument('-i','--interactive', help='start interactive mode', action="store_true" )
    parser.add_argument('-a','--analysisid', help='specify analysis id [ATLAS-SUSY-2019-08]', 
            type=str, default="ATLAS-SUSY-2019-08" )
    args = parser.parse_args()

    # anaid = "ATLAS-SUSY-2019-08"
    anaid = args.analysisid
    estimator = CovMatrixEstimator ( anaid )
    if args.download:
        estimator.download ( True )
    if args.patch:
        estimator.patch ( )
    if args.write:
        matrix = estimator.retrieveMatrix ()
        estimator.store()
    else:
        estimator.load()
        estimator.createSModelSInfo()
    if args.interactive:
        estimator.interact()
