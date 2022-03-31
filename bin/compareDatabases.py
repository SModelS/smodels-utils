#!/usr/bin/env python

""" compare systematically two different databases. 
    write out differences. """

from __future__ import print_function
import sys
from smodels.experiment.databaseObj import Database 
from smodels.experiment.txnameObj import TxNameData
from smodels.experiment.expResultObj import ExpResult
from smodels.tools.colors import colors
from smodels.tools.physicsUnits import fb
import os
colors.on = True
TxNameData._keep_values = True

tx = { "tot": 0, "err": 0 }

def error ( text, col=colors.red ):
    print ( "%s%s%s" % ( col, text, colors.reset ) )
    tx["err"]+=1

def getPath ( text ):
    return text[text.rfind("/")+1:]

def unequal ( a, b, label=None ):
    if abs ( a- b ) / a > 1e-3:
        l = ""
        if label:
            l=label
        print ( "unequal %s: old,new = %f, %f -->" % ( l,a,b ) )
        return True
    return False

def compareMatrices ( ER, DS, txname, a, b ):
    if a.shape != b.shape:
        error ( "the _Vs have different shapes!!" )
        return
    return
    dx = 0.
    for x in range ( a.shape[0] ):
        for y in range ( a.shape[1] ):
            dx += abs ( abs(b[x][y]) - abs(a[x][y]) )
    dx = dx / ( a.shape[0]*a.shape[1] )
    if ( dx > 1e-3 ):
    # if ( sum(sum( a != b ) ) ):
        error ( "Data differ in _V: %s/%s/%s: dx=%.2f" % ( ER, DS, txname, dx ) )
        #print ( type(a) )
        print ( a )
        print ( b )
        #sys.exit(-1)

def discussTxName ( ER, DS, oldTx, newTx ):
    tx["tot"]+=1
    fail = False
    checkedTriples = [ ("CMS-PAS-SUS-16-024","data","TChiWZoff"),
    ]
    checkedTriples = []
    for Z in checkedTriples:
        if (ER, DS, oldTx.txName) == Z:
            error ( "skipping %s/%s/%s" % ( ER, DS, oldTx.txName ), colors.green )
            return
    checkedPairs = [ ("CMS-SUS-13-013", "T1ttttoff"), 
        ("CMS-SUS-13-012", "TChiZZ"), 
        ("CMS-SUS-13-012", "TChiWW"), 
        ("CMS-SUS-13-012", "TChiWZ"), 
        ("CMS-SUS-13-012", "T5WWoff"), 
        ("CMS-SUS-13-012", "T5WW"), 
    #    ("CMS-SUS-13-012", "T5"), 
        ("ATLAS-SUSY-2013-04", "T2tt"),
        ("ATLAS-SUSY-2013-11","TSlepSlep" ),
        ("ATLAS-SUSY-2013-11","TChiWW" ),
        ("ATLAS-SUSY-2013-11","TChipChimSlepSnu" ),
    ]
    checkedPairs = [ ]
    for Z in checkedPairs:
        if (ER, oldTx.txName) == Z:
            error ( "skipping %s/%s/%s" % ( ER, DS, oldTx.txName ), colors.green )
            return
    # print ( "txname: %s/%s:%s" % ( ER, DS, oldTx.txName ) )
    if ( oldTx.txnameData != newTx.txnameData ):
        error ( "dataInfos differ!" )
        tx["err"]+=1
        #sys.exit(-1)
    #print ( type ( oldTx.txnameData._V ) )
    #import IPython
    #IPython.embed()
    compareMatrices ( ER, DS, oldTx.txName, oldTx.txnameData._V, newTx.txnameData._V )
    #if ( oldTx.txnameData._1dim != newTx.txnameData._1dim ):
    #    error ( "txnameData differ in _1dim! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        # sys.exit(-1)

    ## xsecs
    #oldUnit = oldTx.txnameData.unit 
    #if type(oldUnit)!=int:
    #    oldUnit = oldUnit.asNumber (fb)
    #newUnit = newTx.txnameData.unit
    #if type(newUnit)!=int:
    #    newUnit = newUnit.asNumber (fb)
    oldUnit, newUnit = 1., 1.
    if ( unequal ( oldUnit * sum ( oldTx.txnameData.y_values ), newUnit * sum (newTx.txnameData.y_values ), "xsec" ) ):
        error ( "--> txnameData differ in xsec! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        error ( "    ::: n(entries)=%d, %d" % ( len ( oldTx.txnameData.xsec ), len ( newTx.txnameData.xsec ) ) )
        error ( " :ov=%s" % oldTx.txnameData.value[:88] )
        error ( " :nv=%s" % newTx.txnameData.value[:88] )
        #sys.exit(-1)
        fail=True

    ## delta_x
    if ( unequal ( sum ( sum ( oldTx.txnameData.delta_x ) ),\
                   sum ( sum (newTx.txnameData.delta_x ) ), "delta_x" ) ):
        error ( "--> txnameData differ in delta_x! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        fail=True
        #sys.exit(-1)

    if ( oldTx.constraint != newTx.constraint ):
        error ( "txname differs in constraint! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        fail=True
        #sys.exit(-1)
    if ( oldTx.condition != newTx.condition ):
        error ( "txname differs in condition! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        fail=True
        #sys.exit(-1)
    #if ( oldTx.conditionDescription != newTx.conditionDescription ):
    #    error ( "txname differs in conditionDescription! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
    #    fail=True
    if fail:
        tx["err"]+=1
        #sys.exit(-1)

def oldTxNotInNew ( ER, DS, Tx ):
    error ( f"The txname {ER}/{DS}/{Tx.txName} appears in the first DB, but not in the second." )

def newTxNotInOld ( ER, DS, Tx ):
    error ( f"The txname {ER}/{DS}/{Tx.txName} appears in the second DB, but not in the first.", colors.green )

def discussDSs ( ER, oldDS, newDS ):
    oldTxs=oldDS.txnameList
    oldTxDict = { getPath ( x.path ):x for x in oldTxs }
    newTxs=newDS.txnameList
    newTxDict = { getPath ( x.path ):x for x in newTxs }
    if False:
        print ( "%s, %s: %d txnames" % ( ER, oldDS.path[oldDS.path.rfind("/")+1:],
                   len(oldTxs) ) )
        print ( "%s, %s: %d txnames" % ( ER, newDS.path[oldDS.path.rfind("/")+1:],
                   len(newTxs) ) )
    for k,v in oldTxDict.items():
        if not k in newTxDict.keys():
            oldTxNotInNew ( ER, oldDS.path[oldDS.path.rfind("/")+1:], v )
        else:
            discussTxName ( ER, oldDS.path[oldDS.path.rfind("/")+1:], \
                            v, newTxDict[k] )
    for k,v in newTxDict.items():
        if not k in oldTxDict.keys():
            newTxNotInOld ( ER, oldDS.path[oldDS.path.rfind("/")+1:], v )

def oldDSNotInNew ( er, r ):
    error ( "The dataset %s/%s appears in the first DB, but not in the second." % \
            ( er, getPath ( r.path ) ) ) 

def newDSNotInNew ( er, r ):
    error ( "The dataset %s/%s appears in the second DB, but not in the first." % \
            ( er, getPath ( r.path ) ), colors.green )

def discussERs ( oldER, newER, anaid ):
    oldDSs = oldER.datasets
    oldDSDict = { getPath ( x.path):x for x in oldDSs }
    newDSs = newER.datasets
    newDSDict = { getPath ( x.path):x for x in newDSs }
    if False:
        print ( "anaid", anaid )
        print ( "oldER: %s, %d datasets" % (oldER.globalInfo.id,len(oldDSs) ) )
        print ( "newER: %s, %d datasets" % (newER.globalInfo.id,len(newDSs) ) )
    for k,v in oldDSDict.items():
        if not k in newDSDict.keys():
            oldDSNotInNew ( oldER.globalInfo.id, v )
        else:
            discussDSs ( oldER.globalInfo.id, v, newDSDict[k] )
    for k,v in newDSDict.items():
        if not k in oldDSDict.keys():
            newDSNotInNew ( oldER.globalInfo.id, v )

def oldResultNotInNew ( r ):
    """ there is an old result that does not appear in the new database """
    error ( "The analysis %s appears in the first DB, but not in the second." % \
            r.globalInfo.id, colors.yellow )

def newResultNotInNew ( r ):
    """ there is a new result that does not appear in the old database """
    error ( "The analysis %s appears in the second DB, but not in the first." % \
            r.globalInfo.id, colors.yellow )

def createDictionary ( er ):
    ret = {}
    for x in er:
        Id = x.globalInfo.id
        if len(x.datasets)==1 and x.datasets[0].dataInfo.dataId==None:
            Id+=":ul"
        else:
            Id+=":eff"
        ret[Id]=x
    return ret

def discussDBs ( oldD, newD ):
    if True:
        print ( "old: %s" % oldD )
        print ( "new: %s" % newD )

    oldER = oldD.getExpResults ( useSuperseded=False, useNonValidated=False )
    oldERDict = createDictionary ( oldER )
    newER = newD.getExpResults ( useSuperseded=False, useNonValidated=False )
    newERDict = createDictionary ( newER )

    for k,v in oldERDict.items():
        if not k in newERDict.keys():
            oldResultNotInNew ( v )
        else:
            discussERs ( v, newERDict[k], k )
    for k,v in newERDict.items():
        if not k in oldERDict.keys():
            newResultNotInNew ( v )

    print ( "%d/%d txnames failed." % ( tx["err"], tx["tot"] ) )

def compare():
    import argparse
    ap = argparse.ArgumentParser( description="compare two databases" )
    ap.add_argument('-d1', '--database1', help='name of first database [~/git/smodels-database]', default="~/git/smodels-database" )
    ap.add_argument('-d2', '--database2', help='name of second database [official]', default="official" )
    args = ap.parse_args()
    args.database1 = os.path.expanduser ( args.database1 )
    args.database2 = os.path.expanduser ( args.database2 )

    #oldDname = "/home/walten/git/branches/smodels-database"
    #newDname = "/home/walten/git/smodels-database"

    #if False:
    #    oldDname = "/home/walten/git/branches/smodels/test/database"
    #    newDname = "/home/walten/git/smodels/test/database"

    oldD = Database ( args.database1 )
    newD = Database ( args.database2 )

    discussDBs ( oldD, newD )

if __name__ == "__main__":
    compare()
