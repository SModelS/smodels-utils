#!/usr/bin/env python3

"""
.. module:: rerunOlderValidations
   :synopsis: rerun only validations that are older

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import glob, os, time, sys

def apr18(): ## unix time stamp for april 18
    return time.time()-60*60*24*5

def loadDatabase():
    from smodels.experiment.databaseObj import Database
    db  = Database ( "../../smodels-database/" )
    return db

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

def scan():
    db = loadDatabase()
    dictfiles = glob.glob ( "../../smodels-database/*TeV/*/*/validation/T*.py")
    topos = False
    if "13" in sys.argv:
        dictfiles = glob.glob ( "../../smodels-database/13TeV/*/*/validation/T*.py")
    if "-t" in sys.argv:
        topos = True
    anas, anantopos = set(), set()
    for d in dictfiles:
        D = d.replace("../../smodels-database/","")
        m = os.stat ( d ).st_mtime
        dt = m - apr18()
        p = D.find ( "/validation" )
        ana = D[:p]
        pr = ana.rfind("/")
        ana = ana[pr+1:]
        anaNTopo = getAnaTopo ( D )
        vstat = getValidationStatus(d.replace("../../smodels-database/",""),db)
        if vstat != "True":
            continue
        # print ( "d",d, getValidationStatus(d.replace("../../smodels-database/",""),db) )
        if dt < 0.:
            anas.add ( ana )
            anantopos.add ( anaNTopo )
    print ( ",".join ( anas ) )
    # print ( "\n".join ( anas ) )
    if topos:
        print ( "\n".join ( anantopos ) )
    print ( f"{len(anas)} analyses need to rerun" )

if __name__ == "__main__":
    scan()
