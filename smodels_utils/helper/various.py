#!/usr/bin/env python3

"""
.. module:: various
    :synopsis: various helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os, sys

def getPathName ( dbpath, analysis, valfile = None ):
    """ get the path name, given a dbpath, an analysis id, and a valfile name
        potentially with wildcards 
    :param dbpath: database path, e.g ~/git/smodels-database
    :param valfile: if None, get path to analysis folder, else path to validation file
    """
    import glob
    dbpath = os.path.expanduser ( dbpath )
    if type(valfile)==str and not valfile.endswith(".py"): valfile += ".py"
    # analysis = analysis.replace("agg"," (agg)" )
    experiment = "ATLAS"
    if "CMS" in analysis:
        experiment = "CMS"
    sqrts = 8
    if not dbpath.endswith ( "/"):
        dbpath += "/"
    for sqrts in [ 8, 13, 14, -1 ]:
        anadir = "%s%dTeV/%s/%s" % ( dbpath, sqrts, experiment, analysis )
        if os.path.exists ( anadir ):
            break
    if sqrts == -1:
        print ( "[various] could not find analysis %s. Did you forget e.g. '-eff' at the end?" % analysis )
        sys.exit()
    folder = "%s%dTeV/%s/%s" % ( dbpath, sqrts, experiment, analysis )
    if valfile == None:
        return folder
    ipath = "%s/validation/%s" % ( folder, valfile )
    files = glob.glob ( ipath )
    if len(files)==0:
        print ( "could not find validation file %s" % ipath )
        sys.exit()
    if len(files)>1:
        print ( "[helper/various] globbing %s resulted in %d files. please specify." % ( ipath, len(files) ) )
        for f in files[:2]:
            p = f.rfind("/")
            if p > 0:
                f = f[p+1:]
            print ( "[helper/various] found: %s" % ( f ) )
        sys.exit()
    ipath = files[0]
    return ipath

def hasLLHD ( analysis ) :
    """ can one create likelihoods from analyses?
        true for efficiency maps and upper limits with expected values. """
    if len ( analysis.datasets)>1:                                                            return True
    ds=analysis.datasets[0]
    if ds.dataInfo.dataType=="efficiencyMap":
        return True
    for tx in ds.txnameList:
        if tx.hasLikelihood():
            return True
    return False

def getValidationModule ( dbpath, analysis, validationfile ):
    """ get the validation module from the path to database, analysis name,
        name of validation file (with globs) 
    :param dbpath: database path, e.g. ~/git/smodels-database
    :param analysis: analysis name, e.g. ATLAS-SUSY-2019-08
    :param validationfile: validationfile, e.g. TChiWH_2EqMassAx_EqMassBy_combined.py
		:returns: validationData
    """
    dbpath = os.path.expanduser ( dbpath )
    ipath = getPathName ( dbpath, analysis, validationfile )
    validationData = getValidationModuleFromPath ( ipath, analysis )
    return validationData

def getValidationModuleFromPath ( ipath, analysis ):
    """ knowing the path to the validation file, extract validationData """
    import importlib
    try:
        spec = importlib.util.spec_from_file_location( "validationData", ipath )
        imp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imp)
        imp.ana = analysis
    except Exception as e:
        print ( "Could not import validation file 1: %s" % e )
    return imp


if __name__ == "__main__":
    print ( "This machine has %d CPUs" % nCPUs() )
