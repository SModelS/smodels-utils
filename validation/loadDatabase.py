#!/usr/bin/env python3

from smodels.experiment.databaseObj import Database
from smodels.base.smodelsLogging import setLogLevel

setLogLevel ( "debug" )

dbpath = "../../smodels-database"
# dbpath = "https://smodels.github.io/database/official222pre1"
# dbpath = "https://smodels.github.io/database/official222pre1+https://smodels.github.io/database/fastlim222pre1+https://smodels.github.io/database/superseded222pre1+https://smodels.github.io/database/nonaggregated222pre1"
db = Database ( dbpath, subpickle = True )
print ( db )
