#!/usr/bin/env python3

""" setup rundir, pythonpaths. Mostly for CLIP. """

import os, sys

def setup():
    codedir = "/mnt/hephy/pheno/ww/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    home = os.environ["HOME"]
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
            rundir = rundir.replace ( "~", home )
            os.chdir ( rundir )
        return rundir
    if os.path.exists ( "%s/rundir.conf" % home ):
        with open ( "%s/rundir.conf" % home ) as f:
            rundir = f.read().strip()
            rundir = rundir.replace ( "~", home )
            os.chdir ( rundir )
        return rundir
    return ""
