#!/usr/bin/env python3

"""
.. module:: patchesFromSModelS
   :synopsis: neat trick to hack into PyhfUpperLimitComputer to force it
   to write out the patched json files. use like runSModelS.py!

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

from smodels.statistics.pyhfInterface import PyhfUpperLimitComputer, PyhfData

def writePatchedJsons ( data : PyhfData, workspaces ) -> bool:
    """ debug method to write out patched json files.
    :param computer: the upper limit computer
    :returns: true if something was written
    """
    import json
    for workspace,(jsonFile,SRs) in zip(workspaces,data.jsonFiles.items()):
        filename = jsonFile.replace(".json","_patched.json")
        # filename = f"{self.data.globalInfo.id}_{filename}"
        print ( f"[patchesFromSModelS] dumping patched version of {jsonFile} to {filename}" )
        # workspace._comment = self.data.globalInfo.id
        with open ( filename, "wt" ) as f:
            json.dump ( workspace, f, indent=2 )
        f.close()
    return True

oldWsMaker = PyhfUpperLimitComputer.wsMaker

def newWsMaker ( self, apriori : bool = False ) -> list: 
    """ this is our replacement wsMaker method. it calls the old wsMaker method,
    but then (potentially) writes out the workspaces.
    """
    ws = oldWsMaker ( self, apriori )
    if apriori:
        # for now lets not write out the a priori versions
        return ws
    if not hasattr ( self, "scale" ): #  or abs ( self.scale - 1 ) < 1e-5:
        # we want to write out only the first patched version, the others are due to rescaling
        # (i think)
        writePatchedJsons ( self.data, ws )
    return ws

PyhfUpperLimitComputer.wsMaker = newWsMaker

from smodels.tools.runSModelS import main
main()
