#!/usr/bin/env python

"""
.. module:: uprootTools
        :synopsis: Collection of methods used in the context of uproot

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def getExclusionLine ( dirname, topo, axes = "[[x, y], [x, y]]",
                       expected = False, pm = "", verbose = True ):
    """ retrieve exclusion line, as dictionary of coordinates
    :param dirname: directory to search sms.root for
    :param axes: e.g. [[x, y], [x, y]]
    :param expected: if True, get expected line, else observed
    :param pm: plus or minus one? empty is central value, "P1" is
               plus one, "M1" is minus one
    """
    import uproot, os
    dirname = os.path.expanduser ( dirname )
    smsfile = dirname
    if not smsfile.endswith ( "sms.root" ):
        smsfile = os.path.join ( dirname, "sms.root" )
    if not os.path.exists ( smsfile ):
        if verbose:
            print ( f"[uprootTools] cannot find {smsfile}. skip it." )
        return None
    F = uproot.open(smsfile)
    if pm in [ "p", "p1", "+" ]:
        pm = "P1"
    if pm in [ "m", "m1", "-" ]:
        pm = "M1"
    exclname = f"obsExclusion{pm}"
    if expected:
        exclname = f"expExclusion{pm}"
    K = f"{topo}/{exclname}_{axes};1" ## for now we hardcode this
    if not K in F:
        if verbose:
            print ( f"[uprootTools] cannot find {K} in file. skip it." )
        return None
    graph = F[K]
    x = graph.members["fX"]
    y = graph.members["fY"]
    return { "x": x.tolist() ,"y": y.tolist() }

if __name__ == "__main__":
    """ as a script, we simply print out the paths """
    dbpath = "~/git/smodels-database/"
    dirname = f"{dbpath}13TeV/ATLAS/ATLAS-SUSY-2018-04/"
    el = getExclusionLine ( dirname, "TStauStau" )
    print ( "Exclusion line", el["x"][:3], el["y"][:3] )
