#!/usr/bin/env python3

"""
.. module:: databaseLoader
   :synopsis: When running the complete test suite, we need to
              load the database only once

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
setLogLevel("info")
database = Database("../../smodels-database/", useNonValidated=True, discard_zeroes = True )

if __name__ == "__main__":
    print ( database )
