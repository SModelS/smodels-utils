#!/usr/bin/env python3

"""
.. module:: mergeMaps
   :synopsis: Merges the efficiency maps of eg T1, T2, TGQ, into TGQ12.
              Needed for validation only.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function
from smodels.experiment.databaseObj import Database
from smodels.base.physicsUnits import GeV
import sys
import IPython

def getWeights ( mgluino, msquark ):
    """ get the weights for T1, T2, TGQ production, normalized to 1. """
    # return { "T1": 1/3, "T2": 1/3, "TGQ": 1/3 }
    return { "T1": 1, "T2": 1, "TGQ": 1 }

def getEffs ( maps, mgluino, msquark, mN ):
    """ get the efficiencies for T1, T2, TGQ, for the dataset/masses """
    mT1 = [ [ mgluino * GeV, mN*GeV ], [ mgluino * GeV, mN*GeV ] ]
    mT2 = [ [ msquark * GeV, mN*GeV ], [ msquark * GeV, mN*GeV ] ]
    mTGQ = [ [ mgluino * GeV, mN*GeV ], [ msquark * GeV, mN*GeV ] ]
    e = {}
    e["T1"] = maps["T1"].txnameData.getValueFor(mT1 )
    e["T2"] = maps["T2"].txnameData.getValueFor( mT2 )
    e["TGQ"] = maps["TGQ"].txnameData.getValueFor ( mTGQ )
    return e

def mergeDataset( dataset ):
    """ merge a single dataset """
    maps = {}
    for tx in dataset.txnameList:
        txn = tx.txName
        if txn not in [ "T1", "T2", "TGQ" ]:
            continue
        maps[txn]=tx
    effs = []
    for mgluino in range ( 200, 5050, 100 ):
        for msquark in range ( 200, 5050, 100 ):
            for mN in [ 0, 695, 995 ]:
                e = getEffs ( maps, mgluino, msquark, mN )
                w = getWeights ( mgluino, msquark )
                ew = {}
                for txn in e.keys():
                    if e[txn] == None:
                        continue
                    ew[txn] = e[txn]*w[txn]
                E = sum ( ew.values() )
                effs.append ( ( mgluino, msquark, mN, E ) )
    print ( "[ds] ", dataset )
    return effs

def copyExclusionline ( expRes ):
    """ copy the exclusion line in sms.root """
    smsfile = expRes.globalInfo.path.replace("globalInfo.txt","sms.root" )
    print ( "[mergeMaps] sms file is", smsfile )
    import ROOT, subprocess
    f=ROOT.TFile ( smsfile )
    t = f.Get("TGQ" )
    n = t.GetListOfKeys().GetSize()
    keys = []
    for i in range(n):
        name = t.GetListOfKeys().At(i).GetName()
        keys.append ( f.Get("TGQ/%s" % name ) )
        # keys.append ( t.GetListOfKeys().At(i).Clone() )
    f2 = ROOT.TFile ( "new.root", "recreate" )
    f2.mkdir ("TGQ12" )
    f2.cd ( "TGQ12" )
    for k in keys:
        k.Write()
    f2.Write()
    f2.Close()
    subprocess.getoutput ( "cp new.root %s" % smsfile )

def writeTextFile ( dataset, effs ):
    """ write the TGQ12.txt text file """
    Txname = "%s.txt" % dataset.dataInfo.dataId
    # print ( "path", dataset.dataInfo.path )
    Txname = dataset.dataInfo.path.replace("dataInfo","TGQ12" )
    if True:
        Txname = Txname.replace("branches/","")
    with open ( Txname, "wt" ) as f:
        f.write ( "txName: TGQ12\n" )
        f.write ( "constraint: [[[q]],[[q,q]]]+[[[q]],[[q]]]+[[[q,q]],[[q,q]]]\n" )
        f.write ( "condition: None\n" )
        f.write ( "conditionDescription: None\n" )
        f.write ( "susyProcess: T1+T2+TGQ\n" )
        f.write ( "validated: True\n" )
        f.write ( "finalState: ['MET', 'MET']\n" )
        f.write ( "axes: [[x, 0.0], [y, 0.0]]; [[x, 695.0], [y, 695.0]]; [[x, 995.0], [y, 995.0]]\n" )
        f.write ( "efficiencyMap: [" )
        for ctr,eff in enumerate(effs):
            mgluino, msquark,mN, E= eff
            line = "[[[%.1f*GeV,%.1f*GeV],[%.1f*GeV,%.1f*GeV]],%g]" % \
                    ( mgluino, mN, msquark, mN, E ) 
            if ctr == len(effs)-1:
                line += "]\n"
            else:
                line += ",\n" 
            f.write ( line )

def main():
    # dbpath = "../../../smodels-database"
    dbpath = "/home/walten/git/branches/smodels-database"
    db = Database ( dbpath )
    expRes = db.getExpResults ( analysisIDs = [ "ATLAS-SUSY-2016-07" ],
                                dataTypes = [ "efficiencyMap" ],
                                useNonValidated=True )
    if len(expRes)!= 1:
        print ( "error, I have %d results. dont know what to do" % len(expRes) )
        sys.exit()
    expRes = expRes[0]
    if False:
        copyExclusionline ( expRes )
    # return
    for dataset in expRes.datasets:
        effs = mergeDataset ( dataset )
        writeTextFile ( dataset, effs )
    # IPython.embed()

if __name__ == "__main__":
    main()
