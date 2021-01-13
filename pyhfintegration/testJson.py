"""
Definition of a simple json file with only background numbers
Meant to be use for the unit test
"""

import json
import jsonpatch
import pyhf
modifiers = []
modifiers.append(dict(data=None,
                      type='lumi',
                      name='lumi'))
samples = [dict(name='bkg',
                data=[0.9],
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
                     data=[10])]
bkg =   dict(channels=channels,
            measurements=measurements,
            observations=observations,
            version='1.0.0'
            )

patch = [dict(
    op='add',
    path='/channels/0/samples/0',
    value=dict(
        name='sig',
        data=[0.3],
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
bkg = pyhf.workspace.Workspace(bkg)
ws = pyhf.workspace.Workspace(jsonpatch.apply_patch(bkg, patch))

"""
Trying to get the total bgk numbers out of a workspace object
"""
