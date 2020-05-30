#!/usr/bin/env python3

"""
.. module:: databaseLoader
   :synopsis: When running the complete test suite, we need to
              load the database only once

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys, math
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
import helpers
setLogLevel("info")

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='load and describe database' )
    dbpath = "../../smodels-database/"
    argparser.add_argument ( '--dbpath', help='path to db file', 
                             type=str, default=dbpath )
    args = argparser.parse_args()
    dbpath = args.dbpath
    # dbpath = "./fake1.pcl"
    database = Database( dbpath )
    print ( database )
    # helpers.findLargestExcess ( database )
