
How to run Fastlim
~~~~~~~~~~~~~~~~~~

.. code:: python

    """setup - Import some smodels tools to deal with fastlim"""
    import sys,os
    sys.path.append('../fastlim_tools/runTools')
    home = os.path.expanduser("~")
    sys.path.append(os.path.join(home,'smodels'))
    from smodels.tools.physicsUnits import fb
    from gridFastlim import runFastlim, prepareSLHA
    from fastlimParser import fastlimParser
    from numpy.testing import assert_almost_equal
    from collections import OrderedDict
    
    slhafile = os.path.join(os.getcwd(),'slhaFiles/gluino_squarks.slha')
    outfile = os.path.join(os.getcwd(),'test.sms')
    fastlimdir = os.path.join(os.getcwd(),'../fastlim_tools/fastlim-1.0/')

.. code:: python

    """Run Fastlim and check if the run was successful"""
    run = runFastlim(slhafile,outfile,fastlimdir)
    assert run == True

.. code:: python

    """setup - Convert the output to SModelS format and print output"""
    outdata = open(outfile,'r')
    predictionsDict = eval(outdata.read().replace('\n',''))['ExptRes']
    outdata.close()
    os.remove(outfile)
    resDict = {}
    for res in predictionsDict:
        resDict[res['AnalysisName']] = [res['tval'],res['exptlimit']]

Verify the output
'''''''''''''''''

.. code:: python

    """Define expected output"""
    expectPredictions = {'ATLAS-CONF-2013-024': [1.63E-03,1.76E-01], 'ATLAS-CONF-2013-054': [5.34E-03,4.93E-01], 
                         'ATLAS-CONF-2013-053': [2.49E-05,3.73E-01], 'ATLAS-CONF-2013-037': [7.54E-04,3.67E-01],
                         'ATLAS-CONF-2013-048': [1.43E-04,2.70E-01], 'ATLAS-CONF-2013-062': [8.82E-04,1.48E-01],
                         'ATLAS-CONF-2013-061': [8.46E-04,2.29E-01], 'ATLAS-CONF-2013-047': [4.35E-02,7.64E-01]}
    for pred in resDict:
        assert_almost_equal(resDict[pred],expectPredictions[pred],decimal=3)

