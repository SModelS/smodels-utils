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
pyhfInterface.py is a copy of smodels/smodels/tools/pyhfInterface.py and pyhfTest.py is a simple code that executes the upper limit computation (upper limit on the signal strength modifier) using the onjects defined in pyhfInterface.py.  Upper limit computer works and returns a result.  Tried to find the same upper limit as the official analysis still for the point [900,250,60] (so without using any new BSM patch) but it gives ~30fb instead of 3fb (if mu95 is the mu upper limit at 95% CL, the cross section upper limit can be obtained by doing mu95*sigmaBSM where sigmaBSM is the BSM production cross section).

Another problem: pyhf seems to crash when mu (signal strength modifier) is greater than 10.0, we can't find the upper limit if it's greater than that.
