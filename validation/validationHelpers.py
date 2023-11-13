#!/usr/bin/env python3

"""
.. module:: validationHelpers
    :synopsis: various helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from typing import Union, List, Dict, Text

## what do we set the width of stable particles to,
## for plotting?
widthOfStableParticles = 1e-25

def getAxisType ( axis : Union[Text,Dict,List] ) -> Union[Text,None]:
    """ determine whether a given axis is v2-type ([[x,y],[x,y]]) or v3-type
    { 0: x, 1: y }. FIXME shouldnt be needed once we completed migrated to v3.
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

def getValidationFileContent ( validationfile : str ):
    """ get the content of the validation file, as a dictionary of
        'data' and 'meta'
    :param validation file: filename
    :returns: dictionary with content of validation file
    """
    #Save data to file
    f = open( validationfile, 'r' )
    lines = f.readlines()
    f.close()
    nlines = len(lines)
    txt = "\n".join(lines[:-1])
    if nlines == 1:
        txt = "\n".join(lines[:])
    # print ( "txt", txt )
    ret = {}
    txt = txt.replace("validationData = ","")
    txt = txt.replace("inf,","float('inf'),")
    txt = txt.replace("nan,","float('nan'),")
    data = eval(txt)
    ret["data"] = data
    meta = None
    if len(lines)>1 and lines[-1].startswith ( "meta" ):
        meta = eval(lines[-1].replace("meta = ","").replace("meta=","") )
    ret["meta"]=meta
    return ret

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
