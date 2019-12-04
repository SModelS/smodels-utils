import pyhf
import json

# Opening main workspace file of region A
wspec = json.load(open("RegionA/BkgOnly.json"))
w = pyhf.Workspace(wspec)

# Opening a random patch to be applied on the previous file
patch = json.load(open("RegionA/patch.sbottom_900_250_60.json", "r"))
BSMpatch = json.load(open("patch.bsm.json", "r"))

# Same modifiers_settings as those use when running the 'pyhf cls' command line
msettings = {
    'normsys': {'interpcode': 'code4'},
    'histosys': {'interpcode': 'code4p'},
}

patches = [patch, BSMpatch] # list of patches that will be "successively" applied to the main worskpace file

p = w.model(measurement_name=None, patches=patches, modifiers_settings=msettings)

test_poi = 1.0 # Value of the parameter of interest (POI) which here is the signal strength modifier

result = pyhf.utils.hypotest(test_poi, w.data(p), p, qtilde=True, return_expected_set = True)
print("CLs_exp")
for clsexp in result[1].tolist():
    print(clsexp[0])
print("CLs_obs")
print(result[0].tolist()[0])
