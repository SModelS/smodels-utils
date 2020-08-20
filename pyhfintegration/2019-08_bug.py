#!/usr/bin/env python3

import pyhf
pyhf.set_backend(b"pytorch")
import json
import jsonpatch

with open('1Lbb-likelihoods-hepdata/BkgOnly.json', 'r') as f:
    bkg = json.load(f)
patch = [{'op': 'add', 'path': '/channels/5/samples/0', 'value': {'data': [0.12533750364832918, 0.17221601055053243, 0.42090085914655334], 'modifiers': [{'data': None, 'type': 'normfactor', 'name': 'mu_SIG'}, {'data': None, 'type': 'lumi', 'name': 'lumi'}], 'name': 'bsm'}},
{'op': 'add', 'path': '/channels/6/samples/0', 'value': {'data': [0.01763733883344263, 0.028793559421499824, 0.1071569435610115], 'modifiers': [{'data': None, 'type': 'normfactor', 'name': 'mu_SIG'}, {'data': None, 'type': 'lumi', 'name': 'lumi'}], 'name': 'bsm'}},
{'op': 'add', 'path': '/channels/7/samples/0', 'value': {'data': [0.004158581794495646, 0.031196622934404727, 0.09260258010973071], 'modifiers': [{'data': None, 'type': 'normfactor', 'name': 'mu_SIG'}, {'data': None, 'type': 'lumi', 'name': 'lumi'}], 'name': 'bsm'}},
{'op': 'remove', 'path': '/channels/4'},
{'op': 'remove', 'path': '/channels/3'},
{'op': 'remove', 'path': '/channels/2'},
{'op': 'remove', 'path': '/channels/1'},
{'op': 'remove', 'path': '/channels/0'}]

llhdSpec = jsonpatch.apply_patch(bkg, patch)
msettings = {'normsys': {'interpcode': 'code4'}, 'histosys': {'interpcode': 'code4p'}}
workspace = pyhf.Workspace(llhdSpec)
model = workspace.model(modifier_settings=msettings)
result = pyhf.infer.hypotest( 10., workspace.data(model), model, qtilde=True, return_expected=False)
print(result)
