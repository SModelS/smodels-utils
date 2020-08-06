#!/usr/bin/env python3

import sys
import pyhf
pyhf.set_backend(b"pytorch")
import json
import jsonpatch
import time
import importlib

def simpleJson(bkg, obs):
    """
    Define a simple likelihood model under the json format
    :param bkg: list of bkg numbers
    :param obs: list of ebserved numbers

    :return: a simple likelihood specification as a json dictionary
    """
    #Defining the channels
    modifiers = []
    modifiers.append(dict(data=None,
                          type='lumi',
                          name='lumi'))
    samples = [dict(name='bkg',
                    data=bkg,
                    modifiers=modifiers)]
    channels = [dict(name='SR1',
                     samples=samples)]
    # Defining the measurements
    config = dict(poi='mu_SIG',
                  parameters=[dict(auxdata=[1],
                                   bounds=[[0.915, 1.085]],
                                   inits=[1],
                                   sigmas=[0.017],
                                   name='lumi')])
    measurements = [dict(name='BasicMeasurement',
                         config=config)]
    # Defining the observations
    observations = [dict(name='SR1',
                         data=obs)]
    ws = dict(channels=channels,
              measurements=measurements,
              observations=observations,
              version='1.0.0')
    return ws

bkg = simpleJson([0.8], [10])
signals = [0.4]
# Making the patch by hand
patch = [dict(
    op='add',
    path='/channels/0/samples/0',
    value=dict(
        name='sig',
        data=signals,
        modifiers=[
            dict(
                name='lumi',
                type='lumi',
                data=None
            ),
            dict(
                name='mu_SIG',
                type='normfactor',
                data=None
            )
        ]
    )
)]
## Using the simple json
llhdSpec = jsonpatch.apply_patch(bkg, patch)
## Using a complete json
# with open("sbottom_900_550_60.json", 'r') as f:
#     llhdSpec = json.load(f)
## Computing the cls outside of SModelS with POI = ul, should give 0.95
msettings = {'normsys': {'interpcode': 'code4'}, 'histosys': {'interpcode': 'code4p'}}
workspace = pyhf.Workspace(llhdSpec)
model = workspace.model(modifier_settings=msettings)
for _ in range(10000):
    result = pyhf.infer.hypotest( 1., workspace.data(model), model, qtilde=True, return_expected=False)
