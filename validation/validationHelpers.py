#!/usr/bin/env python3

"""
.. module:: validationHelpers
    :synopsis: various helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os
from typing import Union, List, Dict, Text
from smodels_utils.helper.terminalcolors import *

## what do we set the width of stable particles to,
## for plotting?
widthOfStableParticles = 1e-25

def showPlot ( filename : str ) -> bool:
    """ we were asked to also show <filename>
    :returns: true if succesful
    """
    if not os.path.exists ( filename ):
        return False
    term = os.environ["TERM"]
    import subprocess, distutils.spawn
    for viewer in [ "timg", "see", "display" ]:
        v = distutils.spawn.find_executable( viewer, f"{os.environ['HOME']}/.local/bin:/bin:/usr/bin:/usr/sbin:/usr/local/bin"  )
        if viewer == "timg" and os.path.exists ( "/bin/timg" ):
            # override python install
            v = "/bin/timg"
        if not v:
            continue
        if viewer == "timg" and term == "xterm-kitty":
            v += " -pkitty "
        cmd = f"{v} {filename}"
        import time
        time.sleep(0.1)
        o = subprocess.check_output ( cmd, shell=True )
        print ( f"[showPlot] {cmd}" )
        time.sleep(1.0)
        print ( f"{o.decode('ascii')}" )
        return True
    return False


def getAxisType ( axis : Union[Text,Dict,List] ) -> Union[Text,None]:
    """ determine whether a given axis is v2-type ([[x,y],[x,y]]) or v3-type
    { 0: x, 1: y }. FIXME shouldnt be needed once we completed migration to v3.
    :returns: v2 or v3 or None
    """
    if type(axis)==str:
        from sympy import var
        x,y,z,w = var('x y z w')
        axis = eval(axis)
    if type(axis)==dict:
        return "v3"
    if type(axis)==list:
        if len(axis)==0:
            return None
        if type(axis[0])==list:
            return "v2"
        if type(axis[0])==dict:
            return "v3"
        return None
    return None

def getDefaultModel ( tempdir : str ) -> str:
    """
    given the temp directory with the slha files,
	  find out what model is a good default. if qnumbers are in the
    slha files, then we use the first slha file as the model definition,
    else 'mssm'.

    returns: "mssm", or the first slha file name
    """
    import glob, os
    slhapath = tempdir.replace("/results","")
    files = list ( glob.glob( os.path.join ( slhapath,"*.slha" ) ) )
    if len(files)==0:
        return "share.models.mssm"
    hasQNumbers = False
    f = open ( files[0], "rt" )
    lines = f.readlines()
    f.close()
    for line in lines:
        p1 = line.find("#")
        if p1 > -1:
            line = line[:p1]
        line = line.lower()
        if "qnumbers" in line:
            return files[0]
    return "share.models.mssm"

def prettyAxes( validationPlot ) -> str:
    """ get a description of the axes that works with v2 as well as v3.
    """
    from smodels_utils.helper import prettyDescriptions
    v = getAxisType ( validationPlot.axes )
    if v == "v2":
        return prettyDescriptions.prettyAxesV2 ( validationPlot.txName, validationPlot.axes )
    return prettyDescriptions.prettyAxesV3 ( validationPlot.txName, validationPlot.axes, validationPlot.getDataMap() )

def getNiceAxes ( axes : str ) -> str:
    """ get a representation of axes that is suitable as part of a filename """
    v = getAxisType ( axes )
    if v == "v2":
        from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
        return MassPlane.getNiceAxes ( axes )
    from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane
    return GraphMassPlane.getNiceAxes ( axes )

def axisV2ToV3 ( axisv2 : str ) -> str:
    """ translate a v2 axis to v3 syntax """
    from sympy import var
    x,y,z,w = var("x y z w")
    axisv3 = {}
    ctr = 0
    l = eval (axisv2)
    if type(l)==dict: ## seems like its translated already!
        return axisv2
    for br in l:
        for symb in br:
            ssymb = str(symb).replace(" ","")
            axisv3[ctr]=ssymb
            ctr+=1
    return str(axisv3)

def equal_dicts(d1 : Dict , d2 : Dict , ignore_keys : List) -> bool:
    """ compare two dictionaries, but ignore a list of keys """
    ignored = set(ignore_keys)
    for k1, v1 in d1.items():
        if k1 not in ignored and (k1 not in d2 or d2[k1] != v1):
            return False
    for k2, v2 in d2.items():
        if k2 not in ignored and k2 not in d1:
            return False
    return True

def significanceFromNLLs ( nll_SM : float, nll_BSM : float, ndf : int = 2)->float:
    """ compute the significance Z from the likelihood ratio,

    :param ndf: number of degrees of freedom
    :returns: Z
    """
    import scipy.stats
    import numpy as np
    #if l_SM == 0.:
    #    return float("nan")
    #if l_BSM == 0.:
    #    return float("nan")
    T = max ( 2 * ( nll_SM - nll_BSM ), 0. )
    # Z = np.sqrt ( T )
    p = scipy.stats.chi2.cdf ( T, df=ndf )
    Z = scipy.stats.norm.ppf ( p )
    if Z < -3.:
        Z = -3.
    return Z

def prettyAxesV3 ( axesStr : str ) -> str:
    """ make an axes v3 description readable

    :param axesStr: e.g. {0:'x',1:'0.5*x+0.5*y',2:'y',3:'x',4:'0.5*x+0.5*y',5:'y'}
    :returns: e.g. x_y_60
    """
    axesDict = eval ( axesStr )
    ## this code is a copy of graphMassPlaneObjects. eventually we should
    ## unify
    def isSymmetrical ( axesDict : Dict ) -> bool:
        """ check if dicionary is symmetrical """
        if len(axesDict)%2==1:
            return False ## odd number of entries
        n = int(len(axesDict)/2)
        for i in range(n):
            if axesDict[i] != axesDict[i+n]:
                return False
        return True
    if isSymmetrical ( axesDict ):
        n = int(len(axesDict)/2)
        for i in range(n,2*n):
            axesDict.pop(i)
    saxes = "_".join ( map ( str, axesDict.values() ) )
    saxes =  saxes.replace("*","").replace(",","").replace("(","").replace(")","").replace("0.0","0").replace("1.0","1").replace("._","_")
    saxes += " [GeV]"
    return saxes

def compareTwoAxes ( axis1 : str, axis2 : str ) -> bool:
    """ compare a given two axes, return true if they are identical.
    this aims at being backwards compatible, being able to (loosely)
    compare v2 axes with v3 axes.

    :returns: true, if identical
    """
    from sympy import var
    x,y,z,w = var('x y z w')
    axis1 = str ( eval ( axis1 ) )
    axis2 = str ( eval ( axis2 ) )
    if axis1 == axis2:
        return True
    d1 = eval ( axis1 )
    d2 = eval ( axis2 )
    if type(d1) == dict and type(d2) == list: # canonize order
        d1,d2 = d2,d1
    if type(d1)==list:
        ctr = 0
        for br in d1:
            for symb in br:
                ssymb = str(symb).replace(" ","")
                # print ( "#", ctr, "symb", str(symb), d2[ctr]==ssymb )
                if d2[ctr] != ssymb:
                    return False
                ctr+=1
        return True
    return d1 == d2


def retrieveValidationFile ( filename, tarballname = None ):
    """ retrieve a certain validation file from the right tarball
    :param filename: name of slha file to extract
    :param tarballname: optionally supply name of tarball also
    """
    import os, sys
    if os.path.exists ( filename ):
        return True
    from smodels_utils.SModelSUtils import installDirectory
    tokens = filename.split("_")
    if tarballname == None:
            tarballname = f"{tokens[0]}.tar.gz"
    tarball = f"{installDirectory()}/slha/{tarballname}"
    tarball = tarball.replace("//","/")
    # print ( "filename", filename, os.path.exists ( tarball ), tarball, os.getcwd() )
    if os.path.exists ( tarball ):
        import tarfile
        f= tarfile.open ( tarball )
        f.extract ( filename )
        f.close()
        if os.path.exists ( filename ):
            return True
    return False

def point_in_hull(point, hull, tolerance=1e-12):
    import numpy
    """ return if a given point is within a given hull """
    return all( (numpy.dot(eq[:-1], point) + eq[-1] <= tolerance) for eq in hull.equations)

def findLineNrOfMeta ( lines : list ) -> int:
    """ find the line number that the meta info starts in """
    for i,line in enumerate(lines):
        if line.startswith ( "meta" ):
            return i
    return len(lines)

def getValidationFileContent ( validationfile : str ):
    """ get the content of the validation file, as a dictionary of
        'data' and 'meta'
    :param validation file: filename
    :returns: dictionary with content of validation file
    """
    if validationfile in [ "", None ]:
        return { "data": {}, "meta": {} }
    try:
        #Save data to file
        f = open( validationfile, 'r' )
        lines = f.readlines()
        f.close()
        lMeta = findLineNrOfMeta ( lines )
        nlines = len(lines)
        txt = "\n".join(lines[:lMeta])
        ## if meta is missing, or just one line
        #if nlines == 1 or not lines[lMeta].startswith("meta"):
        #    txt = "\n".join(lines[nlines])
        # print ( "txt", txt )
        ret = {}
        txt = txt.replace("validationData = ","")
        txt = txt.replace("inf,","float('inf'),")
        txt = txt.replace("nan,","float('nan'),")
        data = eval(txt)
        ret["data"] = data
        meta = None
        if len(lines)>1 and lines[lMeta].startswith ( "meta" ):
            txt = "\n".join(lines[lMeta:])
            meta = eval(txt.replace("meta = ","").replace("meta=","") )
        ret["meta"]=meta
        return ret
    except (SyntaxError,ValueError) as e:
        print ( f"[validationHelpers] error when parsing {RED}{validationfile}: {e}{RESET} Please fix manually." )
        import sys; sys.exit()
        # if there is an error, we continue without
        return { "data": {}, "meta": {} }

def shortTxName( txnames : list ):
    """ get a short moniker for the txnames
    :param txnames: list of strings of txnames
    """
    ret = ""
    txnames = list ( set ( txnames ) )
    txnames.sort ( key = lambda x: len(x) )
    for txname in txnames:
        nooff = txname.replace("off","")
        if nooff in ret and not txname in ret:
            ret+="+off"
            continue
        elif not txname in ret:
            ret+=txname
    return ret

def mergeExclusionLines ( lines : list ):
    """ given a list of exclusion lines, merge them,
    return the merged line
    :param lines: list of lines, one line is a dictionary with x and y as keys.
    """
    line = { "x": [], "y": [] }
    for lt in lines:
        l = lt
        if type(l)==list:
            l = mergeExclusionLines ( lt )
        if type(l) != dict:
            continue
        if "points" in l:
            l = l["points"]
        if not "x" in l or not "y" in l:
            continue
        for lx, ly in zip( l["x"], l["y"] ):
            line["x"].append ( lx )
            line["y"].append ( ly )
    return line

def streamlineValidationData ( data : dict )-> str:
    """ clean up the validation data before it goes into the dict file """
    from smodels_utils.helper.various import py_dumps
    data = py_dumps( data, indent=4, stop_at_level = 4, double_quotes = True )
    out = str(data).replace('[fb]','*fb').replace('[pb]','*pb')
    out = out.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
    while "inf" in out:
        out = out.replace("inf,","float('inf')," )
    while "nan" in out:
        out = out.replace("nan,","float('nan')," )
    # out = out.replace( "}, {" , "},\n{" )
    return out

def mergeValidationData ( contents : list ):
    """ given a list of validation contents, return the merged """
    ret = { "data": [], "meta": [] }
    for content in contents:
        vData = content["data"]
        vMeta = content["meta"]
        ret["meta"].append ( vMeta )
        for v in vData:
            ret["data"].append ( v )
    return ret
