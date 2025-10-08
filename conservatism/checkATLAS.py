#!/usr/bin/env python3

from smodels_utils.helper.various import getCollaboration
import os
import numpy as np

def getPyhfObservation ( js_content, pyhfSRname ):
    """ get obsN from the json file content, for signal region
    pyhfSRname """
    barename, idx = pyhfSRname, 0
    if "[" in pyhfSRname:
        p1 = pyhfSRname.find("[")
        barename = pyhfSRname[:p1]
        idx = int(pyhfSRname[p1+1:-1])
    for SR in js_content["observations"]:
        if SR["name"] == barename:
            data = SR["data"]
            return data[idx]
    return None

def getPyhfExpected ( js_content, pyhfSRname ):
    """ get expectedBG from the json file content, for signal region
    pyhfSRname """
    loc, var = 0., 0.
    barename, idx = pyhfSRname, 0
    if "[" in pyhfSRname:
        p1 = pyhfSRname.find("[")
        barename = pyhfSRname[:p1]
        idx = int(pyhfSRname[p1+1:-1])
    for SR in js_content["channels"]:
        if SR["name"] != barename:
            continue
        samples = SR["samples"]
        for sample in samples:
            data = sample["data"]
            mloc = None 
            if type(data) == list:
                mloc = data[idx] 
                loc += mloc
            if type(data) == dict:
                mloc = .5* ( data["hi_data"] + data["lo_data"] )
                loc += mloc
                var1 = (data["hi_data"] - loc)**2
                var2 = (data["lo_data"] - loc)**2
                var += max(var1,var2)
            if "modifiers" in sample:
                for modifier in sample["modifiers"]:
                    # print ( "modifier", modifier )
                    data = modifier["data"]
                    if type(data)==list:
                        var += data[idx]**2
                    if type(data)==dict:
                        if "hi" in data:
                            f = .5*(data["hi"]-data["lo"])
                            tvar = (f * mloc )**2
                            var += tvar
                        if "hi_data" in data:
                            tvar = (.5*(data["hi_data"][idx]-data["lo_data"][idx]))**2
                            var += tvar
    return loc, var

def checkSR ( SR : dict, jsonFile : str, expRes ):
    """ check a single signal region """
    if "type" in SR and SR["type"] == "CR":
        return
    if not "smodels" in SR or SR["smodels"] == None:
        return
    smodelsname = SR["smodels"]
    dataset = expRes.getDataset ( smodelsname )
    ds = { "obsN": dataset.dataInfo.observedN,
        "expectedBG": dataset.dataInfo.expectedBG,
        "bgError": dataset.dataInfo.bgError }
    jsonPath = os.path.join ( expRes.path, jsonFile )
    import json
    pyhfSRname = SR["pyhf"]
    with open(jsonPath,"rt") as f:
        js_content = json.load(f)
    js = { "obsN": getPyhfObservation ( js_content, pyhfSRname ) }
    loc, var = getPyhfExpected ( js_content, pyhfSRname )
    js["expectedBG"] = loc
    js["bgError"] = float ( np.sqrt(var) )
    print ( )
    print ( f"Ana {expRes.globalInfo.id} SR: {smodelsname} <-> {pyhfSRname}" )
    print ( f"dataset {ds}" )
    print ( f"pyhf {js}" )
    overwriteDataset ( dataset, js )

def overwriteDataset ( dataset, js ):
    """ overwrite them all """
    dataset.dataInfo.observedN = int ( js["obsN"] )
    dataset.dataInfo.expectedBG = js["expectedBG"]
    dataset.dataInfo.bgError = js["bgError"]
    # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

def checkATLASResult ( expRes ):
    """ check a single result """
    jsonFiles = expRes.globalInfo.jsonFiles
    for jsonFile, SRs in jsonFiles.items():
        for SR in SRs:
            checkSR ( SR, jsonFile, expRes )

def checkATLAS():
    from smodels.experiment.databaseObj import Database
    dbpath = "official"
    # dbpath = "new.pcl"
    db = Database ( dbpath )
    expResList = db.getExpResults ( dataTypes=["efficiencyMap"] )
    for expRes in expResList:
        coll = getCollaboration ( expRes.globalInfo.id )
        if coll == "CMS":
            continue
        if not hasattr ( expRes.globalInfo, "jsonFiles" ):
            continue
        checkATLASResult ( expRes )
    db.databaseVersion = db.databaseVersion + "pyhf"
    db.createBinaryFile ( "new.pcl" )

if __name__ == "__main__":
    checkATLAS()
