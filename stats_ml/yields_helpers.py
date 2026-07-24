#!/usr/bin/env python3

""" helpers for the whole yields business """

import time
from pathlib import Path

def lock ( oft : str ):
    if not oft.endswith ( ".temp" ):
        oft += ".temp"
    d = { "time": time.time(), "asctime": time.asctime() }
    from ptools.helpers import py_dumps
    ds = py_dumps ( d, indent=4, double_quotes=True )
    with open ( oft, "wt" ) as f:
        f.write ( ds + "\n" )

def unlock ( oft ):
    if not oft.endswith ( ".temp" ):
        oft += ".temp"
    Path ( oft ).unlink ( missing_ok = True )


def outputFile ( mN2, mC1, mN1, options ):
    ret = f"{options['outputdir']}/TChiWZoff_{mN2}_{mN1}_{mC1}_{mN1}"
    return ret

