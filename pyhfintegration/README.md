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

| masses(sbottom, chi2, chi1) [GeV]| official 95% CL UL [fb] | pyhf combined 95% CL UL [fb] | inclusive 95% CL UL [fb] |
|---|---|---|---|
|900,250,60|3|3.2|A : 3.2|
|800,450,60|2|2.07|A : 1.98, C : 1.72|
|900,550,60|0.9|0.99|A : 0.96, C : 6.4|
|1300,950,60|0.3|0.27|A : 0.30, C : 6.4|

If the results is not shown, it's because it was crashing due to the mu bounds problem that is now solved.

- [x] mu bounds problem solved (that was why region B was crashing) : now the upper mu bound grows dynamically if needed.

# Combination of workspaces

The pyhf.workspace.combine method was raising errors : measurements were defined twice in the resulting workspace. I changed a small bit and corrected that problem. This might have been solved by developers in the new release of 4 March 2020.

- [x] try the new pyhf.workspace.combine method of the 0.4.1 pyhf release : doesn't work

# Rescaling

Infinite loop with mass point [[100*GeV, 1*GeV]] and initial rescaling factor of 10 (changing initial factor to 5 for now)

- [ ] need to decrease the rescaling factor when a nan appears during rescaling

# Poor person's combination (ATLAS-SUSY-2018-31)

It appears that ATLAS-SUSY-2018-31 is performing a poor person's combination, i.e., all three regions (A, B and C) have subregions. These subregions then get combined into three seperate "inclusive" likelihoods, amongst which the inclusive regions giving the best expected limit is picked to compute the observed limit.
Such combination will bring small complications. We'v decided we'd rather try getting the pyhf interface to work with ATLAS-SUSY-2018-04 first which doesn't have this kind of poor person's combination.

- [ ] think about a way to perform this poor person's combination

# Testing ATLAS-SUSY-2018-04

We  compute the results of our pyhf interface by feeding the efficiencies of the SModelS database entry for this analysis into our pyhf interface, and compare them with the official results on the [HEPData page](https://www.hepdata.net/record/ins1765529). The value of interest here is the cross section upper limit that we compare with the upper limit of the table `X-section U.L 1` on the HEPData page, giving the upper limit for pair production of combined stau_L and stau_R.

| m(stau) [GeV] | m(chi1) [GeV] | official 95% UL [pb] | pyhf 95% UL [pb] | discrepancy [%]  |
|      ---      |      ---      |         ---          |       ---        |       ---        |
|80             |1              |24.4000               |13.9000           |-43.3             |
|100            |1              |0.6270                |0.7380            |17.7              |
|120            |1              |0.1950                |0.2440            |25.0              |
|120            |40             |0.4950                |0.4750            |-4.2              |
|140            |1              |0.0806                |0.0960            |19.1              |
|140            |40             |0.1250                |0.1510            |20.8              |
|160            |100            |1.1700                |1.3100            |12.3              |
|160            |1              |0.0387                |0.0443            |14.4              |
|160            |40             |0.0487                |0.0574            |17.7              |
|160            |80             |0.2000                |0.2140            |7.2               |
|180            |1              |0.0218                |0.0289            |32.3              |
|180            |40             |0.0267                |0.0322            |20.8              |
|200            |120            |0.1010                |0.1280            |26.2              |
|200            |1              |0.0123                |0.0159            |28.9              |
|200            |40             |0.0145                |0.0190            |31.4              |
|200            |80             |0.0292                |0.0339            |16.1              |
|220            |1              |0.0072                |0.0071            |-0.9              |
|220            |40             |0.0111                |0.0137            |23.3              |
|240            |120            |0.0175                |0.0208            |19.3              |
|240            |160            |0.0927                |0.1110            |19.8              |
|240            |1              |0.0079                |0.0100            |26.9              |
|240            |40             |0.0075                |0.0099            |31.0              |
|240            |80             |0.0113                |0.0115            |1.9               |
|260            |1              |0.0051                |0.0049            |-2.6              |
|260            |40             |0.0066                |0.0076            |16.0              |
|280            |120            |0.0060                |0.0057            |-4.8              |
|280            |160            |0.0168                |0.0198            |17.7              |
|280            |1              |0.0048                |0.0050            |5.9               |
|280            |40             |0.0041                |0.0038            |-8.8              |
|280            |80             |0.0050                |0.0056            |12.1              |
|300            |1              |0.0036                |0.0034            |-4.1              |
|300            |40             |0.0036                |0.0035            |-2.8              |
|320            |120            |0.0046                |0.0041            |-11.1             |
|320            |160            |0.0050                |0.0047            |-7.8              |
|320            |1              |0.0029                |0.0029            |-0.7              |
|320            |40             |0.0030                |0.0028            |-7.5              |
|320            |80             |0.0030                |0.0029            |-3.1              |
|340            |1              |0.0023                |0.0022            |-1.4              |
|340            |40             |0.0024                |0.0024            |-0.9              |
|360            |120            |0.0033                |0.0030            |-8.2              |
|360            |160            |0.0036                |0.0034            |-5.5              |
|360            |1              |0.0022                |0.0022            |-1.7              |
|360            |40             |0.0024                |0.0024            |-3.7              |
|360            |80             |0.0029                |0.0027            |-5.2              |
|380            |1              |0.0021                |0.0021            |-1.1              |
|400            |120            |0.0021                |0.0021            |-1.1              |
|400            |160            |0.0027                |0.0025            |-8.2              |
|400            |1              |0.0020                |0.0020            |-0.5              |
|400            |40             |0.0020                |0.0020            |-2.0              |
|400            |80             |0.0020                |0.0019            |-4.3              |
|440            |120            |0.0019                |0.0018            |-6.0              |
|440            |1              |0.0016                |0.0016            |-2.5              |
|440            |40             |0.0019                |0.0018            |-8.5              |
|440            |80             |0.0017                |0.0016            |-4.9              |
|280            |200            |0.0770                |0.0978            |27.1              |
|320            |200            |0.0140                |0.0145            |3.0               |
|360            |200            |0.0055                |0.0047            |-13.5             |

A discrepancy of about 10-20%, sometimes up to 40% is observed. According to pyhf developers, this could be due to the efficiencies provided for this analysis, which are at truth-level, instead of the reco-level that are used in the offocial analysis.

# To do list

- [x] perform a mass scan over all mass points of ATLAS-SUSY-2018-04 for comparison
- [x] create a SModelS "pyhf" branch off the "develop" branch
- [ ] we add pyhf into smodels/share/requirements.txt
- [ ] in theoryPrediction.py:getLikelihood, we already have two ways of computing the likelihood.
One way is via the simplified likelihoods, the other is via truncated Gaussians from upper limits. We would add a third 
way, interfacing to your code.
- [ ] put your code into smodels/tools. 
- [ ] need to add some code that picks up the json files in smodels/experiment/txnameObj.py 
- [ ] add a unit test
