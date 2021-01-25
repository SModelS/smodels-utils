#!/usr/bin/env python3

"""
.. module:: various
    :synopsis: various helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os, sys

def removeFastlim ( database ):
    """ given a "Database" object, remove the fastlim results """
    newRes = []
    for expRes in database.expResultList:
        contact = "unknown"
        if hasattr ( expRes.globalInfo, "contact" ):
            contact = expRes.globalInfo.contact
        if not "fastlim" in contact:
                newRes.append ( expRes )
    database.expResultList = newRes

def getPathName ( dbpath, analysis, valfile ):
    """ get the path name, given a dbpath, an analysis id, and a valfile name
        potentially with wildcards """
    import glob
    if not valfile.endswith(".py"): valfile += ".py"
    # analysis = analysis.replace("agg"," (agg)" )
    experiment = "ATLAS"
    if "CMS" in analysis:
        experiment = "CMS"
    sqrts = 8
    for sqrts in [ 8, 13, 14, -1 ]:
        anadir = "%s%dTeV/%s/%s" % ( dbpath, sqrts, experiment, analysis )
        if os.path.exists ( anadir ):
            break
    if sqrts == -1:
        print ( "could not find analysis %s. Did you forget e.g. '-eff' at the end?" % analysis )
        sys.exit()
    ipath = "%s%dTeV/%s/%s/validation/%s" % \
             ( dbpath, sqrts, experiment, analysis, valfile )
    files = glob.glob ( ipath )
    if len(files)==0:
        print ( "could not find validation file %s" % ipath )
        sys.exit()
    if len(files)>1:
        print ( "[plotRatio] globbing %s resulted in %d files. please specify." % ( ipath, len(files) ) )
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

if __name__ == "__main__":
    print ( "This machine has %d CPUs" % nCPUs() )
