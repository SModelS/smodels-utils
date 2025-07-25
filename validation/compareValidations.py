#!/usr/bin/env python3

"""
.. module:: compareValidations
   :synopsis: compare all the validations in two given database directories

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import glob, os, sys, copy, subprocess, time
from smodels_utils.helper.terminalcolors import *

def pprint ( *args ):
    f=open("comparison.log","at")
    print ( *args )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def error ( *args ):
    f=open("comparison.log","at")
    print ( RED, *args, RESET )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()
    f=open("errors.log","at")
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def info ( *args ):
    f=open("comparison.log","at")
    print ( GREEN, *args, RESET )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def warn ( *args ):
    f=open("comparison.log","at")
    print ( YELLOW, *args, RESET )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()
    f=open("errors.log","at")
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def getAnaTopo ( f ):
    """ retrieve the analysis id + topo from path name """
    ret = f.replace("/validation/","/")
    ret = ret.replace("13TeV/","").replace("8TeV/","")
    if ret.startswith("CMS/"):
        ret = ret[4:]
    else:
        ret = ret[6:]
    p = ret.find("_")
    ret = ret[:p]
    return ret

def addToOk ( name ):
    f=open("ok.log","at" )
    f.write ( getAnaTopo(name) )
    f.close()


def compareDicts ( d1, d2 ):
    """ compare two dictionaries """
    for k,v1 in d1.items():
        if k == "t":
            continue
        v2 = d2[k]
        if type(v1) == float:
            if v1 == 0. and v2 == 0.:
                return True
            dv = abs ( v2 - v1 ) / ( v1 + v2 )
            if dv > 0.05:
                error ( f"Dicts: {k}: {v1} != {v2}, rel err is {dv:.3f}" )
                return f"in {k}: {v1} != {v2}"
            return "ok"
        if type(v2) == str and "Gamma" in v2:
            v2 = v2.replace("Gamma","g" )
        if v1 != v2:
            error ( f"Dicts: {v1} != {v2}" )
            return f"in {k}: {v1} != {v2}"
    return "ok"

def getValidationStatus ( f, db ):
    """ get the status for a given validation file f
        (eg 13TeV/ATLAS/ATLAS-SUSY-2015-02/validation/T2tt_2EqMassAx_EqMassBy.py) """
    tokens = f.split("/")
    anaId = tokens[2]
    topo = tokens[4]
    p = topo.find("_")
    topo = topo[:p]
    # dtype = "ul" # efficiencyMap or upperLimit
    dtype = "upperLimit"
    if "-eff" in anaId:
        # dtype="em"
        dtype="efficiencyMap"
        anaId = anaId.replace("-eff","")
    # print ( "get val stat for %s:%s[%s]" % ( anaId, topo, dtype ) )
    er = db.getExpResults ( analysisIDs = [ anaId ], txnames = [ topo ], 
                            dataTypes = [ dtype ], useNonValidated = True )
    if len(er)==0:
        return "could not find"
    if len(er)>1:
        return "more than one result"
    return str(er[0].datasets[0].txnameList[0].validated)

def compareDetails ( D1, D2, f ):
    lD1, lD2 = len(D1), len(D2)
    if lD1 < lD2:
        error ( "%s: number of validation points decreased! %d versus %d" % ( f, lD1, lD2 ) )
        return "number of validation points decreased! %d versus %d" % ( lD1, lD2 )
    if lD1 > lD2:
        pprint ( "%s: number of validation points increased! %d versus %d" % ( f, lD1, lD2 ) )
        return "number of validation points increased! %d versus %d" % ( lD1, lD2 )
    for d1,d2 in zip ( D1, D2 ):
        r = compareDicts ( d1, d2 )
        if r!="ok":
            error ( f"{f}: {d1} !=\n{d2}" )
            return r
    return "ok"

def compareValidation ( db1, db2, f ):
    pprint ( f"compare validations {getAnaTopo(f)}" )
    timestamp = os.stat ( db1 + f ).st_mtime
    f1 = open ( db1 + f, "rt" )
    lines = f1.read()
    f1.close()
    if "<<< HEAD" in lines:
        error ( f" ERROR: git conflict in {db1}{f}" )
        return "git conflict"
    vd1 = eval ( lines.replace ( "validationData =", "" ) )
    f2 = open ( db2 + f, "rt" )
    lines = f2.read()
    f2.close()
    if "<<< HEAD" in lines:
        error ( f" ERROR: git conflict in {db2}{f}" )
        return "git conflict"
    vd2 = eval ( lines.replace ( "validationData =", "" ) )
    if vd1 == vd2:
        info ( f"{getAnaTopo(f)}: exactly the same" )
        return "ok"
    else:
        return compareDetails ( vd1, vd2, f )

def compareDatabases ( db1, db2, db ):
    print ( f"compare databases: {db1} with {db2}" )
    subprocess.getoutput ( "mv comparison.log comparison.old" )
    subprocess.getoutput ( "mv errors.log errors.old" )
    subprocess.getoutput ( "mv ok.log ok.old" )
    g1 = glob.glob ( f"{db1}/*TeV/*/*/validation/T*.py" )
    g2 = glob.glob ( f"{db2}/*TeV/*/*/validation/T*.py" )
    valFilesInBoth = set()
    valFilesMissing = set()
    for g in g1:
        gt = g.replace(db1,"")
        g_ = g.replace(db1,db2)
        if g_ in g2:
            valFilesInBoth.add ( gt )
        else:
            valFilesMissing.add ( g_ )
    for g in g2:
        gt = g.replace(db2,"")
        if gt in valFilesInBoth:
            continue
        valFilesMissing.add ( gt )
    print ( f"{len(valFilesInBoth)} validation files found in both databases." )
    print ( "%d validation files found missing in either database." % \
            ( len(valFilesMissing) ) )
    npassed,ntot=0,0
    vl = list(valFilesInBoth)
    vl.sort()
    for f in vl:
        vstatus = getValidationStatus ( f, db )
        if vstatus != "True":
            pprint ( f"skipping {getAnaTopo(f)}: {vstatus}" )
            continue
        res = compareValidation ( db1, db2, f )
        if res == "ok":
            addToOk ( f )
            npassed+=1
        ntot+=1
    print ( "%d/%d validation objects are ok" % ( npassed, ntot ) )

def loadDatabase():
    from smodels.experiment.databaseObj import Database
    db  = Database ( "../../smodels-database/" )
    return db

if __name__ == "__main__":
    db = loadDatabase()
    db1 = "../../smodels-database/"
    db2 = "../../smodels-database-123/"
    compareDatabases ( db1, db2, db )
