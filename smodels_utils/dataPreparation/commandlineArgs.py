#!/usr/bin/env python3

"""
.. module:: commandlineArgs
   :synopsis: some code that is used by convert.py when
              parsing commandline args.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import argparse
import os

def setEnv ( args ):
    """ set a few environment variables, logging level from args """
    if hasattr ( args, "noUpdate" ) and args.noUpdate==True:
        os.environ["SMODELS_NOUPDATE"]="1"
    if hasattr ( args, "resetValidation" ) and args.resetValidation==True:
        os.environ["SMODELS_RESETVALIDATION"]="1"
    from smodels.base.smodelsLogging import setLogLevel
    if hasattr ( args, "verbose" ):
        setLogLevel ( args.verbose )
    from smodels_utils.dataPreparation.inputObjects import DataSetInput
    if hasattr ( args, "ntoys" ):
        from smodels.base.smodelsLogging import logger
        logger.info ( f"Set the number of toys to {int(args.ntoys)}" )
        DataSetInput.ntoys = args.ntoys
