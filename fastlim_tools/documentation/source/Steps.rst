.. index:: Main steps for running Fastlim and performing the validation

.. _steps:


Steps for Validation
====================

The validation procedure consists first on running Fastlim and SModelS
on the same set of SLHA files. The output produced can then be compared
on a file-by-file basis.
In order to run a scan over several SLHA files the package :mod:`validation.singleJob`
can be used. It uses the methods :py:meth:`~runTools.gridFastlim.runFastlimFor`
or :py:meth:`~runTools.gridSmodels.runSmodelSFor` to run either SModelS or Fastlim (see details below).
The output is then compared using the :mod:`validation.compareResults` package.



Generating Fastlim Output
-------------------------

The tools for running Fastlim are stored in :mod:`runTools.gridFastlim`.
The basic tool is :py:meth:`~runTools.gridFastlim.runFastlim`
(see :ref:`runFastlim <runfastlim>` for more details).
It runs Fastlim for a given SLHA file and generates an output file 
formatted according to some specification. The default format is a file containing
a python dictionary (.sms file).


In order to run Fastlim on a folder containing several SLHAfiles,
the method :py:meth:`~runTools.gridFastlim.runFastlimFor` is available.
It uses the multiprocessing module to allow for parallel processing.
After :py:meth:`~runTools.gridFastlim.runFastlimFor` is run, the folder containing
the SLHA files will also contain the respective .sms files with Fastlim output. 

.. _runfastlim:

runFastlim
~~~~~~~~~~

:py:meth:`~runTools.gridFastlim.runFastlim` uses subprocess.Popen to run fastlim-1.0/fastlimMod.py,
which is identical to fastlim.py, except for the suppression of the screen output
and the option to take an arbitrary file name as output.


Once Fastlim is run, the output file is read by  :py:meth:`~runTools.fastlimOutput.fastlimParser`,
which creates a TheoryPredictionList object containing Fastlim output.
Finally, :py:meth:`~runTools.fastlimOutput.formatOutput` is called to write the TheoryPredictionList
as an object to the .sms file.


Generating SModelS Output
-------------------------

The method for generating and storing SModelS output parallels Fastlim's.
The tools are stored in  :mod:`runTools.gridSmodels`.
The basic tool is :py:meth:`~runTools.gridSmodels.runSmodelS`
(see :ref:`runSmodelS <runsmodels>` for more details).
It runs SModelS for a given SLHA file and generates an output file 
formatted according to some specification. The default format is a file containing
a python dictionary (.sms file).


In order to run SModelS on a folder containing several SLHAfiles,
the method :py:meth:`~runTools.gridSmodels.runSmodelSFor` is available.
It uses the multiprocessing module to allow for parallel processing.
After :py:meth:`~runTools.gridSmodels.runSmodelSFor` is run, the folder containing
the SLHA files will also contain the respective .sms files with SModelS output. 


.. _runsmodels:

runSmodelS
~~~~~~~~~~


:py:meth:`~runTools.gridSmodels.runSmodelS` runs the main SModelS steps
(slhaDecomposer.decompose, theoryPrediction.theoryPredictionsFor).
The user can select a subset of the experimental results in the database.
This selection is made internally using the databaseBrowser.
*By default only results with contact = 'fastlim' are used*.

If doXsecs = True, :py:meth:`~runTools.gridSmodels.runSmodelS` will use subprocess.call
to run the runTools.py utility and compute the cross-sections at LO and NLL.

*Mass and invisible compression are always turned on
and the values for sigmacut and the mass compression gap are fixed. 
See* :py:meth:`~runTools.gridSmodels.runSmodelS` *for the values used.*


Once runSmodelS is run, the TheoryPredictionList output file is read by 
:py:meth:`~runTools.fastlimOutput.formatOutput` to write the .sms file.


Comparing the Output
--------------------

After using :py:meth:`~runTools.gridFastlim.runFastlimFor` and
:py:meth:`~runTools.gridSmodels.runSmodelSFor`  to generate the .sms files for Fastlim
and SModelS, the results will already be in the same format (a .sms file containing
a python dictionary).
The method :py:meth:`validation.compareResults.compareFolders` can then be used 
to compare the the two folders containing the .sms files.


The comparison checks for all the keys in the .sms files and compare their values.
The differences are stored in a dictionary, which is returned as the output.
It is possible to select which fields to ignore and how much to allow for numerical
differences.

:py:meth:`validation.compareResults.compareFolders` also checks
for missing results.

In order to check specific results, the :mod:`validation.debugResults` package can be used.
It contains the :py:meth:`validation.debugResults.debugSmodelS` and 
:py:meth:`validation.debugResults.debugFastlim` methods which re-run SModelS and Fastlim
for a specific experimental result/dataset and provides additional information on the output.



Main Issues
-----------