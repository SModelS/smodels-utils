#!/usr/bin/env python3

""" setup rundir, pythonpaths. Mostly for CLIP. """

import os, sys

def setup():
    codedir = "/mnt/hephy/pheno/ww/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
            rundir = rundir.replace ( "~", os.environ["HOME"] )
            os.chdir ( rundir )
        return rundir
    return ""
