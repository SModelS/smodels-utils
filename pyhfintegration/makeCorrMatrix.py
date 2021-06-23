#!/usr/bin/env python3

import pyhf
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'axes.labelsize': 'small'})
import seaborn as sns
import json


def get_parameter_names(model):
    """get the labels of all fit parameters, expanding vectors that act on
    one bin per vector entry (gammas)
    Args:
        model (pyhf.pdf.Model): a HistFactory-style model in pyhf format
    Returns:
        List[str]: names of fit parameters
    """
    labels = []
    for parname in model.config.par_order:
        for i_par in range(model.config.param_set(parname).n_parameters):
            labels.append(
                f"{parname}[{i_par}]"
                if model.config.param_set(parname).n_parameters > 1
                else parname
            )
    return labels


pyhf.set_backend("jax", "minuit")

ws = pyhf.Workspace(json.load(open("atlas_susy_2018_04.json")))
pdf = ws.model()
data = ws.data(pdf)

init = pdf.config.suggested_init()
bounds = pdf.config.suggested_bounds()

asimov = pdf.expected_data(pyhf.tensorlib.astensor(init))

result, result_obj = pyhf.infer.mle.fit(
#    asimov, pdf, fixed_vals=None, return_result_obj=True, return_correlations=True, do_grad=True
    asimov, pdf, return_result_obj=True, return_correlations=True, do_grad=True
)

import IPython
IPython.embed()

correlations = result_obj.corr

mask = np.abs(correlations) < 0.1
np.fill_diagonal(mask, True)
del_indices = np.all(mask, axis=0)
correlations_reduced = np.delete(np.delete(correlations, del_indices, axis=0), del_indices, axis=1)

labels = np.array(get_parameter_names(pdf))[~del_indices].tolist()

fig,ax = plt.subplots(figsize=(10,10))
ax = sns.heatmap(
    correlations_reduced,
    ax=ax,
    vmin=-1,
    vmax=1,
    center=0,
    cmap=sns.diverging_palette(20, 220, n=200),
    square=True,
    xticklabels=labels,
    yticklabels=labels
)
fig.tight_layout()
plt.savefig('corrMatrix.pdf')
