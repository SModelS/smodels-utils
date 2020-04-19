#!/usr/bin/env python3

"""
.. module:: compareValidations
   :synopsis: compare all the validations in two given database directories

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import glob, os, sys

def compareValidation ( db1, db2, f ):
    print ( "compare validations", db1, db2, f )
    sys.exit()

def compareDatabases ( db1, db2 ):
    print ( "compare %s with %s" % ( db1, db2 ) )
    g1 = glob.glob ( "%s/*TeV/*/*/validation/T*.py" % db1 )
    g2 = glob.glob ( "%s/*TeV/*/*/validation/T*.py" % db2 )
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
    print ( "%d validation files found in both databases." % ( len(valFilesInBoth) ) )
    print ( "%d validation files found missing in either database." % \
            ( len(valFilesMissing) ) )
    for f in valFilesInBoth:
        compareValidation ( db1, db2, f )

if __name__ == "__main__":
    db1 = "../../smodels-database/"
    db2 = "../../smodels-database-123/"
    compareDatabases ( db1, db2 )
