#!/usr/bin/env python3

"""
.. module:: various
    :synopsis: various helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os, sys
import logging as logger
from smodels.experiment.expResultObj import ExpResult
from typing import Union, Text, Dict, List
from smodels_utils.helper.terminalcolors import *

def repr_double_quotes(obj):
    import json
    if isinstance(obj, str):
        # Use json.dumps to get a double-quoted string with escapes handled
        return json.dumps(obj)
    elif isinstance(obj, (list, tuple, set)):
        # Preserve type and recursively format elements
        open_bracket, close_bracket = {
            list: ("[", "]"),
            tuple: ("(", ")"),
            set: ("{", "}")
        }[type(obj)]
        inner = ", ".join(repr_double_quotes(x) for x in obj)
        if isinstance(obj, tuple) and len(obj) == 1:  # special case for (x,)
            inner += ","
        return f"{open_bracket}{inner}{close_bracket}"
    elif isinstance(obj, dict):
        items = (f"{repr_double_quotes(k)}: {repr_double_quotes(v)}" for k, v in obj.items())
        return "{" + ", ".join(items) + "}"
    else:
        return repr(obj)

def py_dumps( obj, indent : int = 4, level : int = 0, stop_at_level : int = -1, 
              double_quotes : bool = False ) -> str:
    """ equivalent to json.dumps (ie it pretty prints a given nested structure)
    but tuples are allowed as keys.

    :param indent: number of spaces used for an indentation
    :param level: how many indentations are we in?
    :param stop_at_level: stop indentation at that level, if positive number
    :param double_quotes: use double quotes, like json
    """
    sp = ' ' * (level * indent)
    sp_next = ' ' * ((level + 1) * indent)
    mrepr = repr
    if double_quotes:
        mrepr = repr_double_quotes

    if isinstance(obj, dict):
        if not obj:
            return '{}'
        items = []
        if stop_at_level > 0 and level >= stop_at_level:
            for k, v in obj.items():
                value = f"{py_dumps(v, indent, level + 1, stop_at_level, double_quotes )}"
                items.append(f"{mrepr(k)}: {value}")
            return '{ ' + ', '.join(items) + ' }'
        for k, v in obj.items():
            value = f"{py_dumps(v, indent, level + 1, stop_at_level, double_quotes )}"
            items.append(f"{sp_next}{mrepr(k)}: {value}")
        return '{\n' + ',\n'.join(items) + '\n' + sp + '}'

    elif isinstance(obj, list):
        if not obj:
            return '[]'
        items = [f"{sp_next}{py_dumps(i, indent, level + 1, stop_at_level, double_quotes )}" for i in obj]
        if stop_at_level > 0 and level >= stop_at_level:
            return '[ ' + ', '.join(items) + ' ]'
        return '[\n' + ',\n'.join(items) + '\n' + sp + ']'

    return mrepr(obj)

def checkNumpyVersion ():
    """ for pickling we want numpy < 2.0.0, so that the pickle files work for
    both v1 and v2. """
    import numpy
    if numpy.__version__[0]!="1":
        print ( f"[various] numpy version is {numpy.__version__}. Downgrade to 1.26.4 for pickling:" )
        print ( f"pip install numpy==1.26.4" )
        sys.exit()

def removeAnaIdSuffices ( anaId : str ) -> str:
    """ given  analysis id <anaId>, remove all kinds of suffices """
    for i in [ "-agg", "-eff", "-ma5", "-adl", "-strong", "-ewk", "-multibin", \
               "-hino", "-wino", "-incl", "-trim" ]:
        anaId = anaId.replace(i,"")
    return anaId

def round_to_n ( x : float, n : int ) -> float:
    """ round <x> to <n> significant digits """
    if x in [ None, 0. ]:
        return x
    import math
    if x < 0.:
        return -round(-x, -int(math.floor(math.log10(-x))) + (n - 1))
    return round(x, -int(math.floor(math.log10(x))) + (n - 1))

def getCollaboration ( anaid : Union[Text,Dict] ) -> str:
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

def getYear ( anaId : str ) -> int:
    """ given analysis id <anaId>, determine year
    :param anaId: e.g. 'CMS-SUS-20-004'
    :returns: e.g. 2018
    """
    if anaId.startswith ( "CMS-EXO-16-057" ): # an exceptional case
        return 8
    year = anaId.replace("ATLAS-","").replace("CMS-","").replace("SUSY-","")
    year = year.replace("EXOT-","")
    year = year.replace("EXO-","").replace("SUS-","").replace("PAS-","")
    year = year.replace("CONF-","").replace("CERN-EP-","")
    year = year.replace("CERN-PH-EP-","")
    p1 = year.find("-")
    year = year[:p1]
    return int(year)

def getSqrts ( anaId : str ) -> Union[int,float]:
    """ given analysis id <anaId>, determine sqrts
    :param anaId: e.g. 'CMS-SUS-20-004'
    :returns: e.g. 13 or 13.6
    """
    if anaId.startswith ( "CMS-EXO-16-057" ): # an exceptional case
        return 8
    year = str ( getYear ( anaId ) )
    if year == "20":
        return 13
    if year.startswith("20"):
        year = year[2:]
    year = int ( year )
    if year < 15:
        return 8
    return 13

def findCollaboration ( anaid : str ) -> str:
    """ a trivial convenience function. tell the collaboration name
    from the analysis name """
    if "cms" in anaid.lower():
        return "CMS"
    if "atlas" in anaid.lower():
        return "ATLAS"
    return "???"

def cutPoints ( points, ranges ) -> dict:
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

def getExclusionCurvesForV2(jsonfile,txname=None,axes=None, get_all=False,
                          expected=False, dicts=False, ranges=None ):
    """
    Reads exclusion_lines.json and returns the dictionary objects for the
    exclusion curves, for axes being in SModelS v2 format.
    If txname is defined, returns only the curves
    corresponding to the respective txname. If axes is defined, only
    returns the curves for that axis.
    If root objects are needed, convert via
    smodels_utils.helper.rootTools.exclusionCurveToTGraph

    :param jsonfile: path to exclusion_lines.json file
    :param txname: the TxName in string format (i.e. T1tttt)
    :param axes: the axes definition in string format,
                 e.g. [x, y, 60.0], [x, y, 60.0]] or {0:x,1:y,...}
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
        logger.error( f"json file {jsonfile} not found" )
        oldVersion = jsonfile.replace("exclusion_lines.json","exclusions.json")
        if os.path.exists ( oldVersion ):
            jsonfile = oldVersion
            logger.warning( f"found an old {jsonfile}, trying with that" )
        else:
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
    if type(caxes)==dict:
        from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane
        maxes = GraphMassPlane.getNiceAxes ( maxes )
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
                caxis = constr # eval(constr)
                try:
                    caxis = eval(constr) # for SModelS v2 axes
                except SyntaxError as e:
                    # for SModelS v3 axes
                    caxes = GraphMassPlane.getNiceAxes ( axes )
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


def getExclusionCurvesFor(jsonfile : os.PathLike , txname : Union[str,None]=None,
        axes : Union[str,None]= None, get_all : bool =False,
        expected : bool=False, dicts : bool =False,
        ranges : Union[dict,None] = None ) -> dict:
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
                 e.g. [x, y, 60.0], [x, y, 60.0]] or {0:x,1:y,...}
    :param get_all: Get also the +-1 sigma curves?
    :param expected: if true, get expected, not observed
    :param ranges: if dict, then cut exclusion lines, e.g.
                   { "x": [ 100, 200 ] }
    :param dicts: if true, then do not return lists of lines,
                  but dictionaries instead

    :return: a dictionary, where the keys are the TxName strings
    and the values are the respective dictionaries of coordinates.
    None, if no exclusion lines have been found.
    """
    from validationHelpers import getAxisType
    axisType = getAxisType ( axes )
    if axisType == "v2":
        return getExclusionCurvesForV2 ( jsonfile, txname, axes, get_all, expected,
                dicts, ranges )

    import json
    if not os.path.isfile(jsonfile):
        logger.error( f"json file {jsonfile} not found" )
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
    from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane
    maxes = GraphMassPlane.getNiceAxes ( maxes )

    def match ( name : str ) -> bool:
        """ do we want an exclusion line with this name?
        :param name: e.g. obsExclusionP1_0
        """
        if expected and name.startswith ( "obs" ):
            return False
        if not expected and name.startswith ( "exp" ):
            return False
        if not get_all and "ExclusionP1" in name:
            return False
        if not get_all and "ExclusionM1" in name:
            return False
        return True

    def axisMatch ( jsonDict : dict ) -> bool:
        """ see if the axes match """
        convertedDict = {}
        for k,v in jsonDict.items():
            convertedDict[int(k)]=v
        return convertedDict == caxes

    def axisDescriptionsMatchV3 ( name : str, caxes : Dict ) -> bool:
        """ do these match? v3 version!
        :param name: e.g. obsExclusion_{0:'x',1:'y',2:'y'}
        :param caxes: e.g. {0: 'x', 1: '0.5*x+0.5*y', 2: 'y', 3: 'x',
        4: '0.5*x+0.5*y', 5: 'y'}
        :returns: match or no match
        """
        p1 = name.find("_")
        axes = eval ( name[p1+1:] )
        return axes == caxes

    def axisDescriptionsMatch ( name : str, caxes : Dict ) -> bool:
        """ do these match?
        :param name: e.g. obsExclusion_[[x,y,60.0],[x,y,60.0]]
        :param caxes: e.g. {0: 'x', 1: '0.5*x+0.5*y', 2: 'y', 3: 'x',
        4: '0.5*x+0.5*y', 5: 'y'}
        :returns: match or no match
        """
        if "{" in name: ## we have a type v3 axis name!!
            return axisDescriptionsMatchV3 ( name, caxes )
        p1 = name.find("_")
        axisInName = eval ( name[p1+1:] )
        def flatten ( nested : List ) -> List:
            temp = [item for row in axisInName for item in row]
            ret = []
            last = []
            for t in temp:
                if type(t) in [ tuple ]:
                    ret.append ( t[0] )
                    last.append ( t[1] )
                else:
                    ret.append ( t )
            for t in last:
                ret.append ( t )
            return ret
        flattened = flatten ( axisInName )

        import sympy
        x,y,z,w = sympy.var('x y z w')
        for k,v in caxes.items():
            e1 = sympy.parse_expr ( str(v) )
            e2 = sympy.parse_expr ( str(flattened[k]) )
            if e1 != e2:
                return False
        return True

    for txn,content in content.items():
        if txname != None and txn != txname:
            continue
        for name,line in content.items():
            if not match ( name ):
                continue
            if not axisDescriptionsMatch ( name, caxes ):
                continue
            if "axisMap" in line and not axisMatch ( line["axisMap"] ):
                continue
            points = cutPoints ( line, ranges )
            if not txn in ret:
                ret[txn]=[]
                if dicts:
                    ret[txn]={}
            if dicts:
                ret[txn][name]= points
            else:
                ret[txn].append( { "points": points, "name": name } )
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
    # for backwards compatibility
    return getValidationDataPathName ( dbpath, analysis, valfile)

def getValidationDataPathName ( dbpath : os.PathLike, analysis : str ,
        valfile : str, validationFolder : str = "validation" ):
    """ get the path name, given a dbpath, an analysis id, and a valfile name
        potentially with wildcards
    :param dbpath: database path, e.g ~/git/smodels-database
    :param valfile: if None, get path to analysis folder,
                    else path to validation file
    """
    import glob
    dbpath = os.path.expanduser ( dbpath )
    if dbpath.endswith ( ".pcl" ):
        p = dbpath.rfind("/")
        dbpath = dbpath[:p]
    if type(valfile)==str and not valfile.endswith(".py"): valfile += ".py"
    # analysis = analysis.replace("agg"," (agg)" )
    experiment = "ATLAS"
    if "CMS" in analysis:
        experiment = "CMS"
    sqrts = 8
    if not dbpath.endswith ( "/"):
        dbpath += "/"
    for sqrts in [ 8, 13, 14, -1 ]:
        anadir = f"{dbpath}{sqrts}TeV/{experiment}/{analysis}"
        if os.path.exists ( anadir ):
            break
    if sqrts == -1:
        if not analysis.endswith  ( "-eff" ):
            oldana = analysis
            analysis += "-eff"
            for sqrts in [ 8, 13, 13.6, 14, -1 ]:
                anadir = f"{dbpath}{sqrts}TeV/{experiment}/{analysis}"
                if os.path.exists ( anadir ):
                    print ( f"[various] added -eff to '{oldana}'." )
                    break
            if sqrts == -1:
                print ( f"[various] could not find analysis {oldana}, nor {oldana}-eff." )
                sys.exit()
        else:
            print ( f"[various] could not find analysis {analysis}." )
    folder = f"{dbpath}{sqrts}TeV/{experiment}/{analysis}"
    if valfile == None:
        return folder
    ipath = f"{folder}/{validationFolder}/{valfile}"
    files = glob.glob ( ipath )
    if len(files)==0:
        print ( f"[various] could not find validation file {RED}{ipath}{RESET}" )
        return None
        # sys.exit()
    if len(files)>1:
        print ( f"[helper/various] globbing {ipath} resulted in {len(files)} files. please specify." )
        for f in files[:2]:
            p = f.rfind("/")
            if p > 0:
                f = f[p+1:]
            print ( f"[helper/various] found: {f}" )
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
        print ( f"[various] Could not import validation file {ipath}: {e}" )
        sys.exit()
    return imp


if __name__ == "__main__":
    #from smodels.base.runtime import nCPUs
    #print ( "This machine has %d CPUs" % nCPUs() )
    print ( "srqts", getSqrts ( "CMS-EXO-16-057" ) )
