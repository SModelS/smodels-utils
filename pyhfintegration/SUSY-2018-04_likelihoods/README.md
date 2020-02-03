# JSON Likelihoods for ATLAS SUSY direct staus analysis

The JSON likelihoods are serialized for each region: [Region-combined](Region-combined), [Region-lowMass](Region-lowMass), and [Region-highMass](Region-highMass). This is done by providing a background-only workspace containing the signal/control/validation channels for each region at `$region/BkgOnly.json` as well as patch files for each mass point on the signal phase-space explored in the analysis. `Region-combined` is a combined fit of the low mass and high mass regions, both of which are provided separately as well.

Each [jsonpatch](http://jsonpatch.com/) file follows the format `$region/patch.DS_mst_mn2_Staus.json` where `mst` is the mass of the stau slepton and `mn2` is the mass of the second-lightest neutralino. Each patch file is named based on the name of the signal sample patched into the background-only workspace. For example, `patch.DS_400_40_Staus.json` means that the signal sample `DS_400_40_Staus` will be patched in.

## Producing signal workspaces

As an example, we use [python jsonpatch](https://python-json-patch.readthedocs.io/en/latest/) here:

```
jsonpatch Region-combined/BkgOnly.json Region-combined/patch.DS_400_40_Staus.json > Region-combined/staus_DS_400_40.json
```

## Computing signal workspaces

For example, with [pyhf](https://diana-hep.org/pyhf/), you can do any of the following:

```
pyhf cls Region-combined/BkgOnly.json -p Region-combined/patch.DS_400_40_Staus.json

jsonpatch Region-combined/BkgOnly.json Region-combined/patch.DS_400_40_Staus.json | pyhf cls

pyhf cls Region-combined/staus_DS_400_40.json
```

# Removed Regions

Two mass points were removed due to the lack of sensitivity on the signal:

- (100, 60)
- (120, 80)

As there was no expected signal in the signal regions, these would not participate in the fit and are not useful to preserve/publish.
