# a folder for our work on integrating pyhf in SModelS

we start working on [SUSY-2018-31](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2018-31/)

we start with the point (900,250,60) of region A (see HEPData_workspaces folder)
The production cross section of sbottom pair production with m=900 GeV is 12.7 fb. 
The acceptances for this point are for the successive SRs : (0.10129, 0.62799, 0.57807) %
The efficiencies for this point are for the successive SRs : (152.08, 99.97, 81.258) %
Total efficiency (efficiency*acceptance) : (0.154, 0.628, 0.470) %

patch_test.py writes a json patch (patch.bsm.json) supposed to be used to replace the signal yields by our own BSM yields (random values for now).
cls_test.py computes the CLs using the previous patch

Seems to work technically when running cls_test.py, no error is raised and the CLs are returned.
However, using the same patches but out of box (with the 'pyhf cls' command line) seems to give different CLs.
