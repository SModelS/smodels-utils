#!/usr/bin/env python3

import pyhf
import json

import simplify
from simplify import yields

pyhf.set_backend(pyhf.tensorlib, "minuit")

def simplifyMe():
    spec = json.load(open("likelihood.json", "r"))
    spec['measurements'][0]["config"]["poi"] = "lumi"

    model, data = simplify.model_tools.model_and_data(spec)

    fixed_params = model.config.suggested_fixed()
    init_pars = model.config.suggested_init()
    # run fit
    asimov = True
    fit_result = simplify.fitter.fit( model, data, init_pars=init_pars, 
                                      fixed_pars = fixed_params, asimov = asimov )
    exclude_process = []

    ylds = yields.get_yields(spec, fit_result, exclude_process)

    dummy_signal = False
    # Hand yields to simplified LH builder and get simplified LH
    newspec = simplify.simplified.get_simplified_spec(
       spec, ylds, allowed_modifiers=[], prune_channels=[], include_signal=dummy_signal
    )

    output_file = "simplified.json"
    with open ( output_file, "w+" ) as out_file:
        json.dump(newspec, out_file, indent=4, sort_keys=True)

if __name__ == "__main__":
    simplifyMe()
