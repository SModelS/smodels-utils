#!/usr/bin/env python

""" compare systematically two different databases. 
    write out differences. """

from __future__ import print_function
from smodels.experiment.databaseObj import Database 
from smodels.experiment.expResultObj import ExpResult
from smodels.tools.colors import colors
from smodels.tools.physicsUnits import fb
colors.on = True

tx = { "tot": 0, "err": 0 }

def error ( text, col=colors.red ):
    print ( "%s%s%s" % ( col, text, colors.reset ) )

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

def discussTxName ( ER, DS, oldTx, newTx ):
    tx["tot"]+=1
    fail = False
    # print ( "txname: %s/%s:%s" % ( ER, DS, oldTx.txName ) )
    if ( oldTx.txnameData.dataTag != newTx.txnameData.dataTag ):
        error ( "!dfojd" )
        #sys.exit(-1)
    #print ( type ( oldTx.txnameData._V ) )
    #import IPython
    #IPython.embed()
    if ( sum(sum(oldTx.txnameData._V != newTx.txnameData._V ) ) ):
        error ( "txnameData differ in _V: %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        #sys.exit(-1)
    if ( oldTx.txnameData._1dim != newTx.txnameData._1dim ):
        error ( "txnameData differ in _1dim! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        # sys.exit(-1)

    ## xsecs
    oldUnit = oldTx.txnameData.unit 
    if type(oldUnit)!=int:
        oldUnit = oldUnit.asNumber (fb)
    newUnit = newTx.txnameData.unit
    if type(newUnit)!=int:
        newUnit = newUnit.asNumber (fb)
    if ( unequal ( oldUnit * sum ( oldTx.txnameData.xsec ), newUnit * sum (newTx.txnameData.xsec ), "xsec" ) ):
        error ( "--> txnameData differ in xsec! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        error ( "    ::: n(entries)=%d, %d" % ( len ( oldTx.txnameData.xsec ), len ( newTx.txnameData.xsec ) ) )
        # error ( "units= %s %s" % ( oldUnit, newUnit ) )
        #sys.exit(-1)
        fail=True

    ## delta_x
    if ( unequal ( sum ( sum ( oldTx.txnameData.delta_x.A ) ),\
                   sum ( sum (newTx.txnameData.delta_x.A ) ), "delta_x" ) ):
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
    if ( oldTx.conditionDescription != newTx.conditionDescription ):
        error ( "txname differs in conditionDescription! %s/%s/%s" % ( ER, DS, oldTx.txName ) )
        fail=True
    if fail:
        tx["err"]+=1
        #sys.exit(-1)

def oldTxNotInNew ( ER, DS, Tx ):
    error ( "The txname %s/%s/%s appears in the old DB, but not in the new." % \
            ( ER, DS, Tx.txName ) )
def newTxNotInOld ( ER, DS, Tx ):
    error ( "The txname %s/%s/%s appears in the new DB, but not in the old." % \
            ( ER, DS, Tx.txName ), colors.green )

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
    error ( "The dataset %s/%s appears in the old DB, but not in the new." % \
            ( er, getPath ( r.path ) ) ) 

def newDSNotInNew ( er, r ):
    error ( "The dataset %s/%s appears in the new DB, but not in the old." % \
            ( er, getPath ( r.path ) ), colors.green )

def discussERs ( oldER, newER ):
    oldDSs = oldER.datasets
    oldDSDict = { getPath ( x.path):x for x in oldDSs }
    newDSs = newER.datasets
    newDSDict = { getPath ( x.path):x for x in newDSs }
    if False:
        print ()
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
    error ( "The result %s appears in the old DB, but not in the new." % \
            r.globalInfo.id, colors.yellow )

def newResultNotInNew ( r ):
    """ there is a new result that does not appear in the old database """
    error ( "The result %s appears in the new DB, but not in the old." % \
            r.globalInfo.id, colors.yellow )

def discussDBs ( oldD, newD ):
    if False:
        print ( "old: %s" % oldD )
        print ( "new: %s" % newD )

    oldER = oldD.getExpResults ( useSuperseded=True, useNonValidated=True )
    oldERDict = { x.globalInfo.id:x for x in oldER }
    newER = newD.getExpResults ( useSuperseded=True, useNonValidated=True )
    newERDict = { x.globalInfo.id:x for x in newER }
    for k,v in oldERDict.items():
        if not k in newERDict.keys():
            oldResultNotInNew ( v )
        else:
            discussERs ( v, newERDict[k] )
    for k,v in newERDict.items():
        if not k in oldERDict.keys():
            newResultNotInNew ( v )

    print ( "%d/%d txnames failed." % ( tx["err"], tx["tot"] ) )

oldDname = "/home/walten/git/branches/smodels-database"
newDname = "/home/walten/git/smodels-database"

if False:
    oldDname = "/home/walten/git/branches/smodels/test/database"
    newDname = "/home/walten/git/smodels/test/database"

oldD = Database ( oldDname )
newD = Database ( newDname )

discussDBs ( oldD, newD )
