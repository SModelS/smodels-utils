import pyhf
import json

# Opening main workspace file of region A
wspec = json.load(open("RegionA/BkgOnly.json"))
ws = pyhf.Workspace(wspec)

# Opening a random patch to be applied on the previous file
patch = json.load(open("RegionA/patch.sbottom_1200_1195_60.json"))

msettings = {
    'normsys': {'interpcode': 'code4'},
    'histosys': {'interpcode': 'code4p'},
}

patches = [patch] # patches in the next method must be a list (it is possible to specify several patches)

mdl = ws.model(measurement_name=None, patches=patches, modifiers_settings=msettings)

test_poi = 1.0 # Don't know yet what is that parameter

result = pyhf.utils.hypotest(test_poi, ws.data(mdl), mdl, qtilde=True, return_expected_set = True)
print("CLs_obs")
print(result[0].tolist()[0])
print("CLs_exp")
for cl in result[1].tolist():
    print(cl[0])
