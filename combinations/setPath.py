#!/usr/bin/env python

""" this sets the path so we can write e.g. 
    "from smodels_utils.plotting import blah """

from __future__ import print_function

def configure():
    """ get the path name of this file, remove setPath.py, 
        remove the last subdir, the remaining string should be the
        base path name """
    import sys, os
    curpath = os.path.abspath(".")
    p = curpath.find("smodels-utils")
    ret="../" ## fallback, if no smodels-utils is found
    if p > -1:
        ret = curpath[:p+14]
    sys.path.append ( ret )
    from smodels_utils import SModelSUtils
    SModelSUtils.addInstallDirectory()
    SModelSUtils.addSModelSPath()
    return ret
    

configure()

if __name__ == "__main__":
    print ( configure() )
