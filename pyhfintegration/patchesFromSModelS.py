#!/usr/bin/env python3
# coding: utf-8

from smodels.statistics.pyhfInterface import PyhfUpperLimitComputer

def writePatchedJsons ( computer : PyhfUpperLimitComputer, workspaces ) -> bool:
    """ debug method to write out patched json files.
    :param computer: the upper limit computer
    :returns: true if something was written
    """
    import json
    for workspace,(jsonFile,SRs) in zip(workspaces,computer.data.jsonFiles.items()):
        filename = jsonFile.replace(".json","_patched.json")
        # filename = f"{self.data.globalInfo.id}_{filename}"
        print ( f"[patchesFromSModelS] dumping patched version of {jsonFile} to {filename}" )
        # workspace._comment = self.data.globalInfo.id
        with open ( filename, "wt" ) as f:
            json.dump ( workspace, f, indent=2 )
        f.close()
    return True

oldWsMaker = PyhfUpperLimitComputer.wsMaker

def newWsMaker ( self, apriori = False ): 
    ws = oldWsMaker ( self, apriori )
    writePatchedJsons ( self, ws )
    return ws

PyhfUpperLimitComputer.wsMaker = newWsMaker

from smodels.tools.runSModelS import main
main()
