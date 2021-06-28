#!/usr/bin/env python

"""
.. module:: uprootTools
        :synopsis: Collection of methods used in the context of uproot

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def getExclusionLine ( dirname, topo ):
    import uproot, os
    """ retrieve exclusion line, as dictionary of coordinates """
    dirname = os.path.expanduser ( dirname )
    smsfile = dirname + "sms.root"
    if not os.path.exists ( smsfile ):
        print ( "[uprootTools] cannot find exclusion line. skip it." )
        return None
    F = uproot.open(smsfile)
    K = f"{topo}/obsExclusion_[[x, y], [x, y]];1" ## for now we hardcode this
    if not K in F:
        print ( f"[uprootTools] cannot find {K} in file. skip it." )
        return None
    graph = F[K]
    x = graph.members["fX"]
    y = graph.members["fY"]
    return { "x": x,"y": y }

if __name__ == "__main__":
    """ as a script, we simply print out the paths """
    dbpath = "~/git/smodels-database/"
    dirname = dbpath + "13TeV/ATLAS/ATLAS-SUSY-2018-04/"
    el = getExclusionLine ( dirname, "TStauStau" )
    print ( "Exclusion line", el["x"][:3], el["y"][:3] )


