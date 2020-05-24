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
dbpath = "../../smodels-database/"
# dbpath = "./fake1.pcl"
database = Database( dbpath )

if __name__ == "__main__":
    print ( database )
    # helpers.findLargestExcess ( database )
