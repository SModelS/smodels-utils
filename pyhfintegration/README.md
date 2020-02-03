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

# Testing the SModelS/pyhfInterface
pyhfInterface.py is a copy of smodels/smodels/tools/pyhfInterface.py and pyhfTest.py is a simple code that executes the upper limit computation (upper limit on the signal strength modifier) using the objects defined in pyhfInterface.py.  
Upper limit computer works and returns a result. Tried to find the same upper limit as the official analysis still for the point [900,250,60] (so without using any new BSM patch) (if mu95 is the mu upper limit at 95% CL, the cross section upper limit can be obtained by doing mu95*sigmaBSM where sigmaBSM is the BSM production cross section, sbottom pair production cross section):  
-official: 3 fb
-with only Region A: 3.2 fb (for regions B and C, pyhf is crashing)  
-by combining all three regions: 3.4 fb

For [800,450,60]:  
-official: 2 fb  
-by combining: 2.O7 fb 1.8 with NLO  
-region A:  1.98 fb 1.72 with NLO / region C: 1.72 fb 14.9 fb (region B is crashing)

For [900,550,60]:  
-official: 0.9 fb  
-by combining: 0.99 fb 0.86 with NLO  
-region A: 0.96 fb 0.84 with NLO / region C: 6.4 fb (region B is crashing)

For [1300,950,60]:  
-official: 0.3 fb  
-by combining: 0.27 fb
-region A: 0.30 fb / region C: 6.4 fb (region B is crashing, solved : now gives 23fb)

mu bounds problem solved (that was why region B was crashing) : now the upper mu bound grows dynamically if needed.

# Replace the data yields with new BSM predictions

Tried to combine regions A, B and C but doesn't work, keeping that for later
