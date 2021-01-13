# JSON Likelihoods for ATLAS SUSY 3L eRJR analysis

The JSON likelihoods are serialized in this folder. This is done by providing a background-only workspace containing the signal/control channels at `BkgOnly.json` as well as patch files for each mass point on the signal phase-space explored in the analysis.

All [jsonpatches](http://jsonpatch.com/) are contained in the file `patchset.json`. Each patch is identified in `patchset.json` by the metadata field `"name":"ERJR_[mn2]_[mn1]"` where `mn2` is the mass of the chargino/second lightest-neutralino and `mn1` is the mass of the lightest supersymmetric particle (LSP).

## Producing signal workspaces

As an example, we use [python jsonpatch](https://python-json-patch.readthedocs.io/en/latest/) and [pyhf](https://scikit-hep.org/pyhf/) here:

```
jsonpatch BkgOnly.json <(pyhf patchset extract patchset.json --name "ERJR_500p0_0p0") > ERJR_500p0_0p0.json
```

## Computing signal workspaces

For example, with [pyhf](https://scikit-hep.org/pyhf/), you can do any of the following:

```
pyhf cls BkgOnly.json -p <(pyhf patchset extract patchset.json --name "ERJR_500p0_0p0") 

jsonpatch BkgOnly.json <(pyhf patchset extract patchset.json --name "ERJR_500p0_0p0") | pyhf cls

pyhf cls ERJR_500p0_0p0.json
```

# Known Issues

These workspaces are the first time that multiple fixed parameters exist in the measurement definition. If using pyhf, take note of this issue [scikit-hep/pyhf#739](https://github.com/scikit-hep/pyhf/issues/739) which will be resolved shortly after these likelihoods are public.
