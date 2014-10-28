#!/usr/bin/env python

""" this sets the path so we can write e.g. "from smodels_tools.tools import blah """

def configure():
    """ get the path name of this file, remove setPath.py,
        remove the last subdir, the remaining string should be the
        base path name """
    import sys, inspect, os
    base=os.path.dirname ( os.path.realpath ( inspect.getabsfile(configure) ) )
    pos=base.rfind("/")
    base=base[:pos+1]
    sys.path.append ( base )
    sys.path.append ( "../" )
    import SModelSTools
    SModelSTools.addInstallDirectory()
    SModelSTools.addSModelSPath()
    return base

configure()

if __name__ == "__main__" :
    print configure()
