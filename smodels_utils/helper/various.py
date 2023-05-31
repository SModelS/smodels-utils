#!/usr/bin/env python3

"""
.. module:: various
    :synopsis: various helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os, sys
import logging as logger
from smodels.experiment.expResultObj import ExpResult
from typing import Union, Text, Dict

def removeAnaIdSuffices ( anaId ):
    """ given  analysis id <anaId>, remove all kinds of suffices """
    x = anaId.replace("-agg","")
    x = x.replace("-strong","").replace("-ewk","")
    return x

def round_to_n ( x, n ):
    """ round x to n significant digits """
    if x in [ None, 0. ]:
        return x
    import math
    if x < 0.:
        return -round(-x, -int(math.floor(math.log10(-x))) + (n - 1))
    return round(x, -int(math.floor(math.log10(x))) + (n - 1))

def getCollaboration ( anaid : Union[Text,Dict] ):
    """ from <anaid> retrieve the collaboration name
    :param anaid: analysis id, like CMS-SUS-17-001, or a dictionary with an "ID"
                  entry
    :returns: CMS or ATLAS
    """
    if type(anaid) == str:
        if "ATLAS" in anaid:
            return "ATLAS"
        if "CMS" in anaid:
            return "CMS"
        return "???"
    collaboration=""
    ID = anaid["ID"]
    if "collaboration" in anaid.keys():
        t = anaid["collaboration"]
        if "ATLAS" in t:
            collaboration = "ATLAS"
        if "CMS" in t:
            collaboration = "CMS"
    else:
        if "ATLAS" in ID:
            collaboration = "ATLAS"
        if "CMS" in ID:
            collaboration = "CMS"
    return collaboration

def getSqrts ( Id : str ):
    """ given analysis id <Id>, determine sqrts """
    year = Id.replace("ATLAS-","").replace("CMS-","").replace("SUSY-","")
    year = year.replace("EXO-","").replace("SUS-","").replace("PAS-","")
    year = year.replace("CONF-","").replace("CERN-EP-","")
    year = year.replace("CERN-PH-EP-","")
    p1 = year.find("-")
    year = year[:p1]
    if year == "20":
        return 13
    if year.startswith("20"):
        year = year[2:]
    year = int ( year )
    if year < 15:
        return 8
    return 13

def cutPoints ( points, ranges ):
    """ cut the points at ranges 
    :param ranges: a dict, e.g. { "x": [0,100], "y": [0,500] }
    :returns: filtered points
    """
    if ranges == None:
        return points
    if not "y" in ranges:
        ranges["y"]=[ float("-inf"), float("inf") ]
    if not "x" in ranges:
        ranges["x"]=[ float("-inf"), float("inf") ]
    if not "y" in points:
        ret = { "x": [] }
        for kx in points["x"]:
            if ranges["x"][0] < kx < ranges["x"][1]:
                    ret["x"].append ( kx )
        return ret

    ret = { "x": [], "y": [] }
    for kx, ky in zip ( points["x"], points["y"] ):
        if ranges["x"][0] < kx < ranges["x"][1] and \
           ranges["y"][0] < ky < ranges["y"][1]:
                ret["x"].append ( kx )
                ret["y"].append ( ky )
    return ret

def getExclusionCurvesFor(jsonfile,txname=None,axes=None, get_all=False,
                          expected=False, dicts=False, ranges=None ):
    """
    Reads exclusion_lines.json and returns the dictionary objects for the
    exclusion curves. If txname is defined, returns only the curves
    corresponding to the respective txname. If axes is defined, only
    returns the curves for that axis.
    If root objects are needed, convert via
    smodels_utils.helper.rootTools.exclusionCurveToTGraph

    :param jsonfile: path to exclusion_lines.json file
    :param txname: the TxName in string format (i.e. T1tttt)
    :param axes: the axes definition in string format,
                 e.g. [x, y, 60.0], [x, y, 60.0]]
    :param get_all: Get also the +-1 sigma curves?
    :param expected: if true, get expected, not observed
    :param ranges: if dict, then cut exclusion lines, e.g. 
                   { "x": [ 100, 200 ] }
    :param dicts: if true, then do not return lists of lines,
                  but dictionaries instead

    :return: a dictionary, where the keys are the TxName strings
            and the values are the respective dictionaries of coordinates.
    """

    import json
    if not os.path.isfile(jsonfile):
        logger.error("json file %s not found" %jsonfile )
        return None

    with open ( jsonfile, "rt" ) as handle:
        content = json.load ( handle )
        handle.close()

    ret = {}
    maxes = axes
    if maxes != None:
        maxes = axes.replace(" ","").strip()
    from sympy import var
    x,y,z,w = var('x y z w')
    caxes = eval ( maxes )
    exp = "obs"
    if expected:
        exp = "exp"
    cnames = [ f"{exp}Exclusion_{maxes}" ]
    if get_all:
        cnames = [ f"{exp}Exclusion_{maxes}", f"{exp}ExclusionP1_{maxes}",
                   f"{exp}ExclusionM1_{maxes}" ]

    # from smodels_utils.helper.rootTools import exclusionCurveToTGraph
    for cname in cnames:
        for txn,content in content.items():
            if txname != None and txn != txname:
                continue
            for axis,points in content.items():
                points = cutPoints ( points, ranges )
                p1 = axis.find("_")
                constr = axis[p1+1:]
                caxis = eval(constr)
                if maxes != None and caxis != caxes: # cname != axis:
                    continue
                # tgraph = exclusionCurveToTGraph ( points, cname )
                if not txn in ret:
                    ret[txn]=[]
                    if dicts:
                        ret[txn]={}
                p2 = cname.find("_")
                if axis[:p1] == cname[:p2]:
                    if dicts:
                        ret[txn][cname]= points
                    else:
                        ret[txn].append( { "points": points, "name": cname } )
        return ret

def mergeExclusionLines ( lines : list ):
    """ given a list of lines, merge them correctly
    """
    ret = {}
    for bulk in lines:
        for txname, line in bulk.items():
            for name,points in line.items():
                if not name in ret:
                    ret[name]=points
                else:
                    ret[name]["x"]+= points["x"]
                    ret[name]["y"]+= points["y"]
    return ret

def getPathName ( dbpath, analysis, valfile = None ):
    """ get the path name, given a dbpath, an analysis id, and a valfile name
        potentially with wildcards
    :param dbpath: database path, e.g ~/git/smodels-database
    :param valfile: if None, get path to analysis folder,
                    else path to validation file
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
        if not analysis.endswith  ( "-eff" ):
            oldana = analysis
            analysis += "-eff"
            for sqrts in [ 8, 13, 14, -1 ]:
                anadir = "%s%dTeV/%s/%s" % ( dbpath, sqrts, experiment, analysis )
                if os.path.exists ( anadir ):
                    print ( f"[various] added -eff to '{oldana}'." )
                    break
            if sqrts == -1:
                print ( "[various] could not find analysis %s, nor %s-eff."% \
                        ( oldana, oldana ) )
                sys.exit()
        else:
            print ( "[various] could not find analysis %s." % analysis )
    folder = "%s%dTeV/%s/%s" % ( dbpath, sqrts, experiment, analysis )
    if valfile == None:
        return folder
    ipath = "%s/validation/%s" % ( folder, valfile )
    files = glob.glob ( ipath )
    if len(files)==0:
        print ( "[various] could not find validation file %s" % ipath )
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

def hasLLHD ( analysis : ExpResult ) -> bool:
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
