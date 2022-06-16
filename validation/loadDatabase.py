#!/usr/bin/env python3

from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel

setLogLevel ( "debug" )

db = Database ( "../../smodels-database", discard_zeroes = False, subpickle = True )
