# a folder for our work on integrating pyhf in SModelS

we start working on [SUSY-2018-31](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2018-31/) with the likelihoods provided on [HEPData](https://www.hepdata.net/record/ins1748602?version=1)

# First tests
we start with the point (900,250,60) of region A (see HEPData_workspaces folder).  
The production cross section of sbottom pair production with m=900 GeV is 12.7 fb.  
The official upper limit is 3 fb.

The acceptances for this point are for the successive SRs : (0.10129, 0.62799, 0.57807) %  The efficiencies for this point are for the successive SRs : (152.08, 99.97, 81.258) %  Total efficiency (efficiency\*acceptance) : (0.154, 0.628, 0.470) %

patch\_test.py writes a json patch (patch.bsm.json) supposed to be used to replace the signal yields by our own BSM yields (random values for now).  
cls\_test.py computes the CLs using the previous patch

Seems to work technically when running cls_test.py, no error is raised and the CLs are returned.
Now cls_test.py returns the same results as the command line (thanks to the answer on the pyhf issues [thread](https://github.com/scikit-hep/pyhf/issues/620))

# Testing pyhfInterface with ATLAS-SUSY-2018-31 offical patches
pyhfInterface.py is a copy of smodels/smodels/tools/pyhfInterface.py and pyhfTest.py is a simple code that executes the upper limit computation (upper limit on the signal strength modifier) using the objects defined in pyhfInterface.py.  
Upper limit computer works and returns a result. Tried to find the same upper limit as the official analysis still for the point [900,250,60] (so without using any new BSM patch) (if mu95 is the mu upper limit at 95% CL, the cross section upper limit can be obtained by doing mu95*sigmaBSM where sigmaBSM is the BSM production cross section, sbottom pair production cross section):  
-official: 3 fb
-with only Region A: 3.2 fb (for regions B and C, pyhf is crashing)  
-by combining all three regions: 3.4 fb

| masses(sbottom, chi2, chi1) [GeV] | official 95% CL UL [fb] | pyhf combined 95% CL UL [fb] | inclusive 95% CL UL [fb] |
|-----------------------------------|-------------------------|------------------------------|--------------------------|
| 900,250,60                        | 3                       | 3.2                          | A : 3.2                  |
| 800,450,60                        | 2                       | 2.07                         | A : 1.98, C : 1.72       |
| 900,550,60                        | 0.9                     | 0.99                         | A : 0.96, C : 6.4        |
| 1300,950,60                       | 0.3                     | 0.27                         | A : 0.30, C : 6.4        |

If the results is not shown, it's because it was crashing due to the mu bounds problem that is now solved.

- [x] mu bounds problem solved (that was why region B was crashing) : now the upper mu bound grows dynamically if needed.

# Combination of workspaces

The pyhf.workspace.combine method was raising errors : measurements were defined twice in the resulting workspace. I changed a small bit and corrected that problem. This might have been solved by developers in the new release of 4 March 2020.

- [x] try the new pyhf.workspace.combine method of the 0.4.1 pyhf release : doesn't work

# Rescaling

Infinite loop with some mass points and initial rescaling factor of 10 (changing initial factor to 5 for now)
- [[100*GeV, 1*GeV]]
- [[440*GeV, 120*GeV]]
- [ ] need to decrease the rescaling factor when a nan appears during rescaling
- [x] detect when the signals come back to a previous identical state

# Poor person's combination (ATLAS-SUSY-2018-31)

It appears that ATLAS-SUSY-2018-31 is performing a poor person's combination, i.e., all three regions (A, B and C) have subregions. These subregions then get combined into three seperate "inclusive" likelihoods, amongst which the inclusive regions giving the best expected limit is picked to compute the observed limit.
Such combination will bring small complications. We'v decided we'd rather try getting the pyhf interface to work with ATLAS-SUSY-2018-04 first which doesn't have this kind of poor person's combination.

- [x] think about a way to perform this poor person's combination (outside of pyhfInterface.py)

# Testing ATLAS-SUSY-2018-04

We  compute the results of our pyhf interface by feeding the efficiencies of the SModelS database entry for this analysis into our pyhf interface, and compare them with the official results on the [HEPData page](https://www.hepdata.net/record/ins1765529). The value of interest here is the cross section upper limit that we compare with the upper limit of the table `X-section U.L 1` on the HEPData page, giving the upper limit for pair production of combined stau_L and stau_R.

| m(stau) [GeV] | m(chi1) [GeV] | official 95% UL [pb] | pyhf 95% UL [pb] | discrepancy [%] |
|---------------|---------------|----------------------|------------------|-----------------|
| 80            | 1             | 24.44300             | 13.85909         | -43.3           |
| 100           | 1             | 0.62703              | 0.73824          | 17.7            |
| 120           | 1             | 0.19548              | 0.24437          | 25.0            |
| 120           | 40            | 0.49516              | 0.47462          | -4.1            |
| 140           | 1             | 0.08059              | 0.09598          | 19.1            |
| 140           | 40            | 0.12468              | 0.15065          | 20.8            |
| 160           | 100           | 1.16810              | 1.31214          | 12.3            |
| 160           | 1             | 0.03869              | 0.04425          | 14.4            |
| 160           | 40            | 0.04872              | 0.05736          | 17.7            |
| 160           | 80            | 0.19953              | 0.21385          | 7.2             |
| 180           | 1             | 0.02181              | 0.02887          | 32.3            |
| 180           | 40            | 0.02668              | 0.03224          | 20.8            |
| 200           | 120           | 0.10116              | 0.12771          | 26.2            |
| 200           | 1             | 0.01232              | 0.01588          | 28.9            |
| 200           | 40            | 0.01445              | 0.01899          | 31.4            |
| 200           | 80            | 0.02917              | 0.03387          | 16.1            |
| 220           | 1             | 0.00720              | 0.00714          | -0.9            |
| 220           | 40            | 0.01114              | 0.01374          | 23.3            |
| 240           | 120           | 0.01747              | 0.02085          | 19.3            |
| 240           | 160           | 0.09266              | 0.11105          | 19.8            |
| 240           | 1             | 0.00786              | 0.00997          | 26.9            |
| 240           | 40            | 0.00754              | 0.00987          | 31.0            |
| 240           | 80            | 0.01125              | 0.01147          | 1.9             |
| 260           | 1             | 0.00507              | 0.00494          | -2.6            |
| 260           | 40            | 0.00656              | 0.00761          | 16.0            |
| 280           | 120           | 0.00604              | 0.00575          | -4.8            |
| 280           | 160           | 0.01679              | 0.01976          | 17.7            |
| 280           | 1             | 0.00476              | 0.00504          | 5.9             |
| 280           | 40            | 0.00414              | 0.00378          | -8.8            |
| 280           | 80            | 0.00502              | 0.00563          | 12.1            |
| 300           | 1             | 0.00355              | 0.00340          | -4.1            |
| 300           | 40            | 0.00356              | 0.00346          | -2.8            |
| 320           | 120           | 0.00458              | 0.00407          | -11.1           |
| 320           | 160           | 0.00505              | 0.00466          | -7.8            |
| 320           | 1             | 0.00292              | 0.00289          | -0.7            |
| 320           | 40            | 0.00303              | 0.00280          | -7.5            |
| 320           | 80            | 0.00302              | 0.00292          | -3.1            |
| 340           | 1             | 0.00226              | 0.00222          | -1.4            |
| 340           | 40            | 0.00239              | 0.00237          | -0.9            |
| 360           | 120           | 0.00331              | 0.00304          | -8.2            |
| 360           | 160           | 0.00356              | 0.00336          | -5.6            |
| 360           | 1             | 0.00220              | 0.00217          | -1.7            |
| 360           | 40            | 0.00244              | 0.00235          | -3.7            |
| 360           | 80            | 0.00288              | 0.00273          | -5.2            |
| 380           | 1             | 0.00209              | 0.00207          | -1.1            |
| 400           | 120           | 0.00210              | 0.00207          | -1.1            |
| 400           | 160           | 0.00268              | 0.00246          | -8.2            |
| 400           | 1             | 0.00202              | 0.00201          | -0.5            |
| 400           | 40            | 0.00200              | 0.00196          | -2.0            |
| 400           | 80            | 0.00197              | 0.00189          | -4.3            |
| 440           | 120           | 0.00191              | 0.00179          | -6.0            |
| 440           | 1             | 0.00162              | 0.00158          | -2.5            |
| 440           | 40            | 0.00192              | 0.00176          | -8.5            |
| 440           | 80            | 0.00172              | 0.00163          | -4.9            |
| 280           | 200           | 0.07698              | 0.09782          | 27.1            |
| 320           | 200           | 0.01404              | 0.01446          | 3.0             |
| 360           | 200           | 0.00547              | 0.00473          | -13.5           |

A discrepancy of about 10-20%, sometimes up to 40% is observed. According to pyhf developers, this could be due to the efficiencies provided for this analysis, which are at truth-level, instead of the reco-level that are used in the official analysis.
- [ ] add another column with best excepted upper limit (problem with nan upper limits)
- [x] try using expected backgrounds of [aux. table 02](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2018-04/tabaux_02.png) : see [ULtab-aux.md](https://github.com/SModelS/smodels-utils/blob/develop/pyhfintegration/ULtab-aux.md)

# Running validation

Validation plots can be found in [validation folder](https://github.com/SModelS/smodels-database/blob/pyhf/13TeV/ATLAS/ATLAS-SUSY-2018-04-eff/validation/) SModelS interface to pyhf is slightly over excluding for ATLAS-SUSY-2018-04 but it is much closer than for the EM vlaidation plot.
For ATLAS-SUSY-2018-31, there are two cases :
- the first mass plane is a bit better than EM but still under excluding
- the second mass plane is worse than EM

# To do list

- [x] add best expected combination in datasetObj.py:getCombinedUpperLimitFor
- [x] added `jsonFiles` attribute into `smodels-utils/smodels_utils/dataPreparation/inputObjects.py`
- [x] implement the likelihood method and interface it to SModelS
- [x] implement the chi2 method and interface it to SModelS
- [x] add a unit test
- [x] integration test
- [ ] some tests failed -> on hold for now
- [x] check if simplified likelihood still works (see testSL.md)
- [x] "forked" covariances/drawBestSRs.py to drawBestCB.py that now takes `combination` instead of `dataset`
  - combined : either pyhf or SL, `dataset` is `(combined)` -> should it be changed given the best expected combination? -> for now, added a `best combination` key in the python output
- [x] add the `best combination` to the `validationData` output
- [ ] validation doesn't really work for ATLAS-SUSY-2018-06 efficiency map
- [ ] validate ATLAS-SUSY-2018-06 and 2019-08 with `pyhf`
- [ ] why ATLAS-SUSY-2018-06 gives same exp and obs UL with pyhf -> two POIs ?
