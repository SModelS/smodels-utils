#!/usr/bin/env python3

import cabinetry
import pyhf
import numpy as np

pyhf.set_backend("numpy", pyhf.optimize.minuit_optimizer(verbose=1))

jsonfile = "example.json"
def download():
    import os, subprocess
    if os.path.exists ( jsonfile ):
        return
    from pyhf.contrib.utils import download
    download("https://www.hepdata.net/record/resource/1406212?view=true", "SUSY-2018-04_likelihoods/" )
    cmd = "jsonpatch SUSY-2018-04_likelihoods/Region-combined/BkgOnly.json SUSY-2018-04_likelihoods/Region-combined/patch.DS_440_80_Staus.json"
    # cmd = "jsonpatch SUSY-2018-04_likelihoods/Region-combined/BkgOnly.json SUSY-2018-04_likelihoods/Region-combined/test.json"
    cmd += f" > {jsonfile}"
    subprocess.getoutput ( cmd )
        
download()

ws = cabinetry.workspace.load( jsonfile )
model, data = cabinetry.model_utils.model_and_data(ws)
channels = model.config.channels

muSigIndex = model.config.parameters.index ( "mu_SIG" )
suggestedBounds = model.config.suggested_bounds()
suggestedBounds[muSigIndex]=(-10.,10.)

result, result_obj = pyhf.infer.mle.fit(
            data, model, return_uncertainties=True, return_result_obj=True,
            par_bounds = suggestedBounds )

# sample parameters from multivariate Gaussian and evaluate model
sampled_parameters = np.random.multivariate_normal(
    result_obj.minuit.values, result_obj.minuit.covariance, size=50000 )
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
print(f"model predictions:\n" )
for i,channel in enumerate ( channels ):
    print ( f" -- {channel}: {yields[i]:.2f}+/-{yield_unc[i]:.2f}" )

np.set_printoptions ( precision = 3 )
ncov = np.cov(model_predictions, rowvar=False)
print(f"covariance:\n{ncov}")
print(f"correlation:\n{np.corrcoef(model_predictions, rowvar=False)}")

indices = np.array ( [ 2,3 ] )
print ( f"covariance of SRs (2,3):\n{ncov[indices[:,None],indices]}" )

indices = np.array ( [ 1,3 ] )
scov = ncov[indices[:,None],indices]
## indices of signal regions
print ( f"covariance of SRs (1,3):\n{scov}" )
for i in indices.tolist():
    ncov[i][i]=ncov[i][i]-yields[i]
scov = ncov[indices[:,None],indices]
print ( f"covariance of SRs w/o Poissonian (1,3):\n{scov}" )

import IPython
IPython.embed( using = False )
