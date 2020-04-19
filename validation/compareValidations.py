#!/usr/bin/env python3

"""
.. module:: compareValidations
   :synopsis: compare all the validations in two given database directories

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import glob

def compare ( db1, db2 ):
    print ( "compare %s with %s" % ( db1, db2 ) )

if __name__ == "__main__":
    db1 = "../../smodels-database/"
    db2 = "../../smodels-database-123/"
    compare ( db1, db2 )
